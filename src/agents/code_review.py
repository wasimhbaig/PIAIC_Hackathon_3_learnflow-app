"""
Code Review Agent
Analyzes student code for correctness, style, efficiency, and readability
"""
from typing import Dict, Any
import structlog

from src.agents.base import BaseAgent

logger = structlog.get_logger()


class CodeReviewAgent(BaseAgent):
    """
    The Code Review Agent provides comprehensive code feedback

    Review Criteria:
    - Correctness: Logic errors, edge cases, bugs
    - Style: PEP 8 compliance, naming conventions
    - Efficiency: Time/space complexity, optimization opportunities
    - Readability: Comments, variable names, code structure
    """

    def __init__(self):
        super().__init__(
            name="code-review",
            purpose="Analyze code for correctness, style, efficiency, and readability",
            model="claude-sonnet-4-5"
        )

    def get_system_prompt(self) -> str:
        return """You are the Code Review Agent for LearnFlow, an AI Python tutoring platform.

Your role is to review student Python code and provide constructive feedback.

**Review Framework** (Score each 0-100):

1. **Correctness** (40% weight)
   - Does the code work as intended?
   - Are there logic errors?
   - Does it handle edge cases?
   - Are there any bugs?

2. **Style** (20% weight)
   - PEP 8 compliance
   - Naming conventions (snake_case for variables/functions, PascalCase for classes)
   - Consistent indentation
   - Appropriate whitespace

3. **Efficiency** (20% weight)
   - Time complexity (Big O)
   - Space complexity
   - Unnecessary operations
   - Optimization opportunities

4. **Readability** (20% weight)
   - Clear variable names
   - Appropriate comments
   - Function documentation
   - Code organization

**Response Structure**:
```
[Overall Assessment]
Great job! Your code works correctly and follows good practices.

✅ **Correctness**: [Score]/100
[Brief assessment and specific issues if any]

⚠️ **Style**: [Score]/100
[Specific style issues with line numbers]

✅ **Efficiency**: [Score]/100
[Complexity analysis and optimization suggestions]

💡 **Readability**: [Score]/100
[Suggestions for improvement]

**Overall Score**: [Weighted Average]/100
**Level**: [Beginner/Learning/Proficient/Mastered]

**Suggestions**:
1. [Specific, actionable suggestion]
2. [Another suggestion]

**Next Steps**:
[Encouragement and what to practice next]
```

**Tone**: Constructive, encouraging, specific. Always start with positives, then suggest improvements.
Be helpful, not harsh. Remember these are students learning."""

    async def process(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Review student code

        Context should include:
            - code: The code to review (required)
            - exercise_id: Optional exercise ID
            - expected_output: Optional expected behavior
            - student_level: Student's proficiency level
        """
        code = context.get("code", "")

        if not code:
            return {
                "content": "Please provide the code you'd like me to review!",
                "metadata": {
                    "agent": "code-review",
                    "error": "No code provided",
                    "confidence": 0.0
                }
            }

        # Build review prompt
        context_str = self.format_context(context)

        full_prompt = f"""{context_str}

Please review this Python code:
```python
{code}
```

{message if message and message != code else "Provide comprehensive feedback."}

Follow the review framework and provide scores for each category."""

        try:
            response = await self.invoke_claude(
                user_message=full_prompt,
                temperature=0.5  # Lower temperature for consistent scoring
            )

            # Extract scores from response (simple regex)
            import re
            scores = {}
            for category in ["Correctness", "Style", "Efficiency", "Readability"]:
                match = re.search(rf"{category}.*?(\d+)/100", response)
                if match:
                    scores[category.lower()] = int(match.group(1))

            # Calculate overall score
            weights = {"correctness": 0.4, "style": 0.2, "efficiency": 0.2, "readability": 0.2}
            overall_score = sum(scores.get(cat, 75) * weight for cat, weight in weights.items())

            logger.info(
                "Code reviewed",
                overall_score=round(overall_score, 1),
                scores=scores,
                code_length=len(code)
            )

            return {
                "content": response,
                "metadata": {
                    "agent": "code-review",
                    "scores": scores,
                    "overall_score": round(overall_score, 1),
                    "confidence": 0.90
                }
            }

        except Exception as e:
            logger.error("Code review failed", error=str(e))
            return {
                "content": "I'm having trouble reviewing your code right now. Please try again.",
                "metadata": {
                    "agent": "code-review",
                    "error": str(e),
                    "confidence": 0.0
                }
            }
