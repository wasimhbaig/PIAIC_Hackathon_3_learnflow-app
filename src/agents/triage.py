"""
Triage Agent
Routes student queries to the appropriate specialist agent
"""
from typing import Dict, Any
import re
import structlog

from src.agents.base import BaseAgent

logger = structlog.get_logger()


class TriageAgent(BaseAgent):
    """
    The Triage Agent analyzes student queries and routes them to specialist agents

    Routing Logic:
    - "explain", "what is", "how does" → Concepts Agent
    - "error", "bug", "not working" → Debug Agent
    - "review my code", "feedback" → Code Review Agent
    - "practice", "exercise", "challenge" → Exercise Agent
    - "progress", "score", "how am I doing" → Progress Agent
    """

    def __init__(self):
        super().__init__(
            name="triage",
            purpose="Route student queries to appropriate specialist agents",
            model="claude-sonnet-4-5"
        )

        # Define routing keywords
        self.routes = {
            "concepts": [
                r"\b(explain|what is|what are|how do|how does|tell me about|teach me)\b",
                r"\b(understand|learn|concept|definition)\b"
            ],
            "debug": [
                r"\b(error|bug|wrong|not working|broken|fix|issue|problem)\b",
                r"\b(traceback|exception|failed|crash)\b"
            ],
            "code-review": [
                r"\b(review|check|feedback|improve|optimize|better)\b",
                r"\b(correct|right|good|style|quality)\b"
            ],
            "exercise": [
                r"\b(practice|exercise|challenge|quiz|test|try)\b",
                r"\b(problem|task|assignment)\b"
            ],
            "progress": [
                r"\b(progress|score|level|mastery|status)\b",
                r"\b(how am i|how\'m i|achievement|streak)\b"
            ]
        }

    def get_system_prompt(self) -> str:
        return """You are the Triage Agent for LearnFlow, an AI Python tutoring platform.

Your role is to analyze student queries and route them to the appropriate specialist agent:

1. **Concepts Agent** - For questions about Python concepts, explanations, and teaching
   Examples: "How do for loops work?", "What is a dictionary?"

2. **Debug Agent** - For error messages, bugs, and troubleshooting
   Examples: "I'm getting a NameError", "My code isn't working"

3. **Code Review Agent** - For code feedback, optimization, and style
   Examples: "Can you review my code?", "How can I improve this?"

4. **Exercise Agent** - For practice problems and coding challenges
   Examples: "Give me a practice problem", "I want to try an exercise"

5. **Progress Agent** - For learning progress, mastery scores, and achievements
   Examples: "How am I doing?", "What's my progress?"

Respond with ONLY the agent name (lowercase) that should handle the query.
If unclear, default to "concepts".

Examples:
User: "How do for loops work?"
Response: concepts

User: "I'm getting a TypeError"
Response: debug

User: "Can you review my function?"
Response: code-review"""

    async def process(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route the message to the appropriate agent

        Returns:
            Dict with:
                - target_agent: Name of the agent to handle the request
                - confidence: Routing confidence (0-1)
                - reasoning: Why this agent was chosen
        """
        message_lower = message.lower()

        # Calculate scores for each agent
        scores = {}
        for agent, patterns in self.routes.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, message_lower))
                score += matches
            scores[agent] = score

        # Get top scoring agent
        top_agent = max(scores, key=scores.get)
        top_score = scores[top_agent]

        # If no clear winner, use Claude for intelligent routing
        if top_score == 0:
            logger.info("No keyword match, using Claude for routing", message=message)

            try:
                response = await self.invoke_claude(
                    user_message=message,
                    max_tokens=10,
                    temperature=0.1  # Low temperature for consistent routing
                )

                # Extract agent name from response
                agent_name = response.strip().lower()

                # Validate agent name
                valid_agents = ["concepts", "debug", "code-review", "exercise", "progress"]
                if agent_name not in valid_agents:
                    logger.warning(
                        "Claude returned invalid agent, defaulting to concepts",
                        returned_agent=agent_name
                    )
                    agent_name = "concepts"

                return {
                    "target_agent": agent_name,
                    "confidence": 0.75,
                    "reasoning": "AI-based routing",
                    "method": "claude"
                }

            except Exception as e:
                logger.error("Claude routing failed, using fallback", error=str(e))
                return {
                    "target_agent": "concepts",
                    "confidence": 0.5,
                    "reasoning": "Fallback due to error",
                    "method": "fallback"
                }

        # Calculate confidence based on score
        max_possible = len(self.routes[top_agent]) * 5  # Assume max 5 keyword matches
        confidence = min(top_score / max_possible, 1.0) if max_possible > 0 else 0.7

        logger.info(
            "Query routed",
            message_preview=message[:50],
            target_agent=top_agent,
            confidence=round(confidence, 2),
            scores=scores
        )

        return {
            "target_agent": top_agent,
            "confidence": confidence,
            "reasoning": f"Keyword-based routing (score: {top_score})",
            "method": "keywords",
            "all_scores": scores
        }
