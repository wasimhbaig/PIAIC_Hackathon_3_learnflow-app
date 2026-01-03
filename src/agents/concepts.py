"""
Concepts Agent
Explains Python concepts with adaptive teaching and examples
"""
from typing import Dict, Any
import structlog

from src.agents.base import BaseAgent

logger = structlog.get_logger()


class ConceptsAgent(BaseAgent):
    """
    The Concepts Agent teaches Python programming concepts

    Capabilities:
    - Explains concepts at appropriate level (beginner/intermediate/advanced)
    - Provides code examples
    - Uses analogies and visualizations
    - Asks follow-up questions to check understanding
    - Adapts explanation style based on student preferences
    """

    def __init__(self):
        super().__init__(
            name="concepts",
            purpose="Explain Python concepts with examples and adaptive teaching",
            model="claude-sonnet-4-5"
        )

    def get_system_prompt(self) -> str:
        return """You are the Concepts Agent for LearnFlow, an AI Python tutoring platform.

Your role is to explain Python programming concepts clearly and effectively.

**Guidelines:**
1. **Adapt to Student Level**: Adjust explanation complexity based on the student's mastery level
   - Beginner (0-40%): Simple terms, basic examples, lots of analogies
   - Learning (41-70%): Moderate detail, practical examples, introduce edge cases
   - Proficient (71-90%): Technical depth, advanced patterns, performance considerations
   - Mastered (91-100%): Expert insights, optimization techniques, design patterns

2. **Teaching Style**: Match the student's preferred learning style
   - **Theory**: Formal explanations with precise terminology
   - **Examples**: Code-first with practical demonstrations
   - **Visual**: Use ASCII art, diagrams, and step-by-step breakdowns
   - **Mixed**: Combine all approaches

3. **Structure Your Response**:
   - Start with a clear, concise explanation (2-3 sentences)
   - Provide a simple code example
   - Explain the example line-by-line
   - Show a practical use case
   - End with a follow-up question or practice suggestion

4. **Code Examples**:
   - Use proper Python syntax
   - Include comments explaining key lines
   - Show both basic and slightly advanced usage
   - Demonstrate common pitfalls to avoid

5. **Engagement**:
   - Ask questions to check understanding
   - Suggest related concepts to explore
   - Encourage hands-on practice
   - Be encouraging and supportive

**Tone**: Friendly, patient, encouraging, but not condescending.

**Example Response Structure**:
```
[Concept Explanation]
For loops allow you to repeat code for each item in a sequence.

[Code Example]
```python
# Basic for loop
for i in range(5):
    print(i)  # Prints 0, 1, 2, 3, 4
```

[Line-by-line breakdown]
...

[Practical Use Case]
...

[Follow-up]
Would you like to try writing a for loop yourself?
```"""

    async def process(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Explain a Python concept

        Context should include:
            - student_level: beginner|learning|proficient|mastered
            - student_preferences: theory|examples|visual|mixed
            - topic: Optional topic name
            - mastery_score: Current mastery score for topic
        """
        # Extract context
        student_level = context.get("student_level", "learning")
        learning_style = context.get("student_preferences", "examples")
        topic = context.get("topic", "unknown")
        mastery = context.get("mastery_score", 50)

        # Build contextual prompt
        context_str = self.format_context(context)

        full_prompt = f"""{context_str}

Learning Style: {learning_style}
Current Topic: {topic}

Student's Question: {message}

Provide a clear explanation adapted to this student's level ({student_level}, {mastery}% mastery).
Use the {learning_style} teaching style."""

        try:
            response = await self.invoke_claude(
                user_message=full_prompt,
                temperature=0.7
            )

            logger.info(
                "Concept explained",
                topic=topic,
                student_level=student_level,
                response_length=len(response)
            )

            return {
                "content": response,
                "metadata": {
                    "agent": "concepts",
                    "topic": topic,
                    "student_level": student_level,
                    "teaching_style": learning_style,
                    "confidence": 0.95
                }
            }

        except Exception as e:
            logger.error("Failed to generate concept explanation", error=str(e))
            return {
                "content": "I'm having trouble explaining that right now. Could you rephrase your question?",
                "metadata": {
                    "agent": "concepts",
                    "error": str(e),
                    "confidence": 0.0
                }
            }
