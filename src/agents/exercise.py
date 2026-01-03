"""
Exercise Agent
Generates and auto-grades coding challenges
"""
from typing import Dict, Any, List
import structlog

from src.agents.base import BaseAgent
from src.config import settings

logger = structlog.get_logger()


class ExerciseAgent(BaseAgent):
    """
    The Exercise Agent creates coding challenges and grades submissions

    Capabilities:
    - Generate topic-specific exercises
    - Adapt difficulty to student level
    - Create test cases for auto-grading
    - Provide hints when students are stuck
    - Grade submissions with detailed feedback
    """

    def __init__(self):
        super().__init__(
            name="exercise",
            purpose="Generate and auto-grade coding challenges",
            model="claude-sonnet-4-5"
        )

    def get_system_prompt(self) -> str:
        return """You are the Exercise Agent for LearnFlow, an AI Python tutoring platform.

Your role is to create engaging coding exercises and grade student submissions.

**When Generating Exercises**:

Response Format:
```json
{
  "title": "Exercise Title",
  "description": "Clear problem description",
  "difficulty": "easy|medium|hard",
  "topic": "Python topic (e.g., 'for loops', 'lists')",
  "starter_code": "# Optional starter code",
  "solution": "# Reference solution",
  "test_cases": [
    {
      "input": "input value or parameters",
      "expected_output": "expected result",
      "hidden": false,
      "description": "What this test checks"
    }
  ],
  "hints": [
    "Hint 1: Gentle guidance",
    "Hint 2: More specific",
    "Hint 3: Almost the answer"
  ]
}
```

**Exercise Guidelines**:
1. **Difficulty Calibration**:
   - Easy: Single concept, clear instructions, 5-15 lines
   - Medium: Multiple concepts, some problem-solving, 15-30 lines
   - Hard: Complex logic, edge cases, optimization, 30+ lines

2. **Clear Instructions**: Be specific about inputs, outputs, and constraints

3. **Test Cases**: Include:
   - Basic case (happy path)
   - Edge case (empty, zero, negative)
   - Complex case (large input)
   - At least one hidden test case

4. **Hints**: Progressive difficulty, don't give away the solution

**When Grading Submissions**:

Response Format:
```
✅ Passed: X/Y test cases

**Test Results**:
1. [Test name]: ✅ Passed
2. [Test name]: ❌ Failed
   Expected: [expected]
   Got: [actual]

**Feedback**:
[Constructive feedback on the solution]

**Score**: X/100
[Beginner|Learning|Proficient|Mastered]

**Suggestions**:
- [How to improve]
```

**Tone**: Encouraging, clear, educational"""

    async def process(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate exercise or grade submission

        For generation, context should include:
            - topic_id: Topic to generate exercise for
            - difficulty: easy|medium|hard
            - student_level: Student's current level

        For grading, context should include:
            - code: Student's submitted code
            - exercise_id: Exercise being attempted
            - test_cases: Test cases to run
        """
        # Determine if this is generation or grading
        if "code" in context and "exercise_id" in context:
            return await self._grade_submission(message, context)
        else:
            return await self._generate_exercise(message, context)

    async def _generate_exercise(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a new coding exercise"""

        topic = context.get("topic", "Python basics")
        difficulty = context.get("difficulty", "medium")
        student_level = context.get("student_level", "learning")

        prompt = f"""Generate a {difficulty} coding exercise on the topic: {topic}

Student level: {student_level}

{message if message else "Create an engaging exercise that tests understanding of this topic."}

Return the exercise in the JSON format specified in your system prompt."""

        try:
            response = await self.invoke_claude(
                user_message=prompt,
                temperature=0.8  # Higher creativity for variety
            )

            logger.info(
                "Exercise generated",
                topic=topic,
                difficulty=difficulty
            )

            return {
                "content": response,
                "metadata": {
                    "agent": "exercise",
                    "action": "generate",
                    "topic": topic,
                    "difficulty": difficulty,
                    "confidence": 0.85
                }
            }

        except Exception as e:
            logger.error("Exercise generation failed", error=str(e))
            return {
                "content": "I'm having trouble generating an exercise. Please try again.",
                "metadata": {
                    "agent": "exercise",
                    "error": str(e),
                    "confidence": 0.0
                }
            }

    async def _grade_submission(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Grade a student's exercise submission"""

        code = context.get("code", "")
        test_cases = context.get("test_cases", [])
        exercise_description = context.get("exercise_description", "")

        prompt = f"""Grade this student submission:

**Exercise**: {exercise_description}

**Student's Code**:
```python
{code}
```

**Test Cases**:
{test_cases}

Evaluate the code, run it mentally against the test cases, and provide detailed grading feedback.
Include what passed, what failed, and constructive suggestions."""

        try:
            response = await self.invoke_claude(
                user_message=prompt,
                temperature=0.3  # Low temperature for consistent grading
            )

            logger.info(
                "Submission graded",
                code_length=len(code),
                test_case_count=len(test_cases)
            )

            return {
                "content": response,
                "metadata": {
                    "agent": "exercise",
                    "action": "grade",
                    "confidence": 0.80
                }
            }

        except Exception as e:
            logger.error("Grading failed", error=str(e))
            return {
                "content": "I'm having trouble grading your submission. Please try again.",
                "metadata": {
                    "agent": "exercise",
                    "error": str(e),
                    "confidence": 0.0
                }
            }
