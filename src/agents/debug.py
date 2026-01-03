"""
Debug Agent
Helps students fix errors with guided hints (not full solutions)
"""
from typing import Dict, Any
import structlog

from src.agents.base import BaseAgent

logger = structlog.get_logger()


class DebugAgent(BaseAgent):
    """
    The Debug Agent helps students fix errors through guided discovery

    Approach:
    - Parse error messages and tracebacks
    - Identify root causes
    - Provide hints, not solutions
    - Guide students to discover the fix themselves
    - Teach debugging strategies
    """

    def __init__(self):
        super().__init__(
            name="debug",
            purpose="Help students fix errors with hints and guidance",
            model="claude-sonnet-4-5"
        )

    def get_system_prompt(self) -> str:
        return """You are the Debug Agent for LearnFlow, an AI Python tutoring platform.

Your role is to help students debug their code WITHOUT giving them the full solution.

**Debugging Philosophy**:
- Help students learn to debug, don't just fix their code
- Provide hints that guide them to discover the solution
- Teach debugging strategies (print debugging, reading tracebacks, etc.)
- Build confidence through successful self-discovery

**Response Structure**:
```
🔍 **Error Analysis**
[Clear explanation of what the error means]

🎯 **Root Cause**
[What's actually causing the problem - without giving the exact fix]

💡 **Hints** (Progressive difficulty):
1. [Gentle hint - direction to look]
2. [More specific hint - narrow down the location]
3. [Strong hint - almost the answer, but they still need to apply it]

🛠️ **Debugging Strategy**
[Teach them how to debug this type of error in the future]

**Try This**: [Specific action they should take to debug]
```

**Common Error Types**:
1. **SyntaxError**: Missing colons, parentheses, quotes
2. **NameError**: Undefined variables, typos
3. **TypeError**: Wrong data types, incompatible operations
4. **IndexError**: List index out of range
5. **IndentationError**: Inconsistent indentation
6. **AttributeError**: Object doesn't have attribute
7. **ValueError**: Invalid value for operation

**Tone**: Encouraging, patient, Socratic. Guide, don't tell.

**Important**:
- NEVER write the corrected code for them
- ALWAYS ask guiding questions
- PROGRESSIVELY reveal hints if they're stuck
- CELEBRATE their thinking process, not just the solution"""

    async def process(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Help debug an error

        Context should include:
            - code: The code with the error (required)
            - error: Error message/traceback (required)
            - previous_attempts: Number of previous failed attempts
            - student_level: Student's proficiency level
        """
        code = context.get("code", "")
        error = context.get("error", "")
        attempts = context.get("previous_attempts", 0)

        if not error and not code:
            return {
                "content": "Please share the error message you're seeing and your code, and I'll help you debug it!",
                "metadata": {
                    "agent": "debug",
                    "error": "Missing error and code",
                    "confidence": 0.0
                }
            }

        # Build debug prompt
        context_str = self.format_context(context)

        # Adjust hint strength based on attempts
        hint_level = "gentle" if attempts < 2 else "specific" if attempts < 4 else "strong"

        full_prompt = f"""{context_str}

Attempt number: {attempts + 1}
Hint level: {hint_level}

Student's message: {message}

Help the student debug this error. Use {hint_level} hints.
{"Since this is their first attempt, be extra gentle and encourage exploration." if attempts == 0 else ""}
{"They've tried a few times, so provide more specific hints." if attempts >= 2 else ""}
{"They're struggling - provide strong hints but still don't give the exact solution." if attempts >= 4 else ""}"""

        try:
            response = await self.invoke_claude(
                user_message=full_prompt,
                temperature=0.6
            )

            logger.info(
                "Debug help provided",
                attempts=attempts,
                hint_level=hint_level,
                has_code=bool(code),
                has_error=bool(error)
            )

            return {
                "content": response,
                "metadata": {
                    "agent": "debug",
                    "hint_level": hint_level,
                    "attempts": attempts + 1,
                    "confidence": 0.88
                }
            }

        except Exception as e:
            logger.error("Debug help failed", error=str(e))
            return {
                "content": "I'm having trouble analyzing that error. Can you share the full error message and your code?",
                "metadata": {
                    "agent": "debug",
                    "error": str(e),
                    "confidence": 0.0
                }
            }
