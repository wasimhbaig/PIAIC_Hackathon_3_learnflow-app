"""
Progress Agent
Tracks and reports student mastery and learning progress
"""
from typing import Dict, Any
import structlog

from src.agents.base import BaseAgent
from src.config import settings

logger = structlog.get_logger()


class ProgressAgent(BaseAgent):
    """
    The Progress Agent monitors student learning and provides progress reports

    Capabilities:
    - Calculate mastery scores
    - Track learning velocity
    - Identify strengths and weaknesses
    - Provide motivational feedback
    - Suggest next learning steps
    """

    def __init__(self):
        super().__init__(
            name="progress",
            purpose="Track mastery scores and provide progress summaries",
            model=settings.ANTHROPIC_MODEL_HAIKU  # Use Haiku for faster, cost-effective responses
        )

    def get_system_prompt(self) -> str:
        return """You are the Progress Agent for LearnFlow, an AI Python tutoring platform.

Your role is to report student learning progress in an encouraging and informative way.

**Mastery Calculation**:
- Exercise Completion: 40%
- Quiz Scores: 30%
- Code Quality: 20%
- Consistency (Streak): 10%

**Mastery Levels**:
- 0-40%: Beginner (🔴 Red)
- 41-70%: Learning (🟡 Yellow)
- 71-90%: Proficient (🟢 Green)
- 91-100%: Mastered (🔵 Blue)

**Response Structure**:
```
📊 **Your Learning Progress**

**Current Module**: [Module Name] - [X]% Complete

**Topic Breakdown**:
- [Topic 1]: [Score]% ([Level]) [Icon]
- [Topic 2]: [Score]% ([Level]) [Icon]
- ...

**Overall Mastery**: [X]%
**Level**: [Current Level]

**Strengths**: 💪
- [What they're doing well]

**Growth Areas**: 📈
- [Where they can improve]

**Streak**: [X] days 🔥
**Recent Activity**: [Summary]

**Recommended Next Steps**:
1. [Specific actionable suggestion]
2. [Another suggestion]

**Motivation**: [Encouraging message based on their progress]
```

**Tone**: Encouraging, specific, data-driven, motivational

**Key Principles**:
1. Always start with achievements
2. Frame weaknesses as "growth opportunities"
3. Be specific with numbers and metrics
4. Provide actionable next steps
5. Celebrate streaks and consistency
6. Compare progress to their own past, not others
7. Make it feel like a game with achievements"""

    async def process(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Provide progress report

        Context should include:
            - student_id: Student UUID
            - mastery_scores: Dict of topic_id -> mastery data
            - current_module: Current module number
            - streak_days: Current learning streak
            - recent_activity: Recent progress events
        """
        student_id = context.get("student_id", "unknown")
        mastery_scores = context.get("mastery_scores", {})
        current_module = context.get("current_module", 1)
        streak_days = context.get("streak_days", 0)

        # Format mastery data for the prompt
        mastery_summary = []
        for topic_id, data in mastery_scores.items():
            topic_name = data.get("topic_name", f"Topic {topic_id}")
            score = data.get("overall_score", 0)
            level = self._get_mastery_level(score)
            mastery_summary.append(f"- {topic_name}: {score}% ({level})")

        mastery_text = "\n".join(mastery_summary) if mastery_summary else "No mastery data yet"

        prompt = f"""Student Progress Data:

**Student ID**: {student_id}
**Current Module**: Module {current_module}
**Streak**: {streak_days} days

**Mastery Scores**:
{mastery_text}

Student's question: {message if message else "Show me my progress"}

Provide an encouraging progress report following the response structure."""

        try:
            response = await self.invoke_claude(
                user_message=prompt,
                temperature=0.6
            )

            logger.info(
                "Progress report generated",
                student_id=student_id,
                current_module=current_module,
                topics_tracked=len(mastery_scores)
            )

            return {
                "content": response,
                "metadata": {
                    "agent": "progress",
                    "student_id": student_id,
                    "current_module": current_module,
                    "streak_days": streak_days,
                    "confidence": 0.92
                }
            }

        except Exception as e:
            logger.error("Progress report failed", error=str(e))
            return {
                "content": "I'm having trouble loading your progress. Please try again.",
                "metadata": {
                    "agent": "progress",
                    "error": str(e),
                    "confidence": 0.0
                }
            }

    def _get_mastery_level(self, score: float) -> str:
        """Convert mastery score to level name"""
        if score < 41:
            return "Beginner 🔴"
        elif score < 71:
            return "Learning 🟡"
        elif score < 91:
            return "Proficient 🟢"
        else:
            return "Mastered 🔵"
