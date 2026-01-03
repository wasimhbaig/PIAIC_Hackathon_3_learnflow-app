"""
Base Agent Class
Foundation for all specialized AI agents in LearnFlow
"""
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import anthropic
import structlog
from datetime import datetime

from src.config import settings

logger = structlog.get_logger()


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents
    Each agent must implement the process() method
    """

    def __init__(
        self,
        name: str,
        purpose: str,
        model: str = settings.ANTHROPIC_MODEL_SONNET
    ):
        self.name = name
        self.purpose = purpose
        self.model = model
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        logger.info(
            "Agent initialized",
            agent_name=self.name,
            model=self.model
        )

    @abstractmethod
    async def process(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a message and return a response

        Args:
            message: The user's message/query
            context: Additional context (student info, topic, code, etc.)

        Returns:
            Dict containing:
                - content: The agent's response
                - metadata: Additional metadata (confidence, suggestions, etc.)
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt that defines this agent's behavior
        """
        pass

    async def invoke_claude(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = settings.ANTHROPIC_MAX_TOKENS,
        temperature: float = 0.7
    ) -> str:
        """
        Invoke Claude API with the given message

        Args:
            user_message: The user's input
            system_prompt: Optional custom system prompt (uses get_system_prompt() if not provided)
            max_tokens: Maximum tokens in response
            temperature: Randomness (0-1)

        Returns:
            Claude's response text
        """
        if system_prompt is None:
            system_prompt = self.get_system_prompt()

        try:
            start_time = datetime.utcnow()

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            duration = (datetime.utcnow() - start_time).total_seconds()

            logger.info(
                "Claude API call successful",
                agent=self.name,
                model=self.model,
                duration_seconds=round(duration, 2),
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens
            )

            return response.content[0].text

        except Exception as e:
            logger.error(
                "Claude API call failed",
                agent=self.name,
                error=str(e),
                exc_info=True
            )
            raise

    def format_context(self, context: Dict[str, Any]) -> str:
        """
        Format context dictionary into a readable string for the prompt
        """
        formatted_parts = []

        if "student_id" in context:
            formatted_parts.append(f"Student ID: {context['student_id']}")

        if "student_level" in context:
            formatted_parts.append(f"Student Level: {context['student_level']}")

        if "topic" in context:
            formatted_parts.append(f"Topic: {context['topic']}")

        if "code" in context:
            formatted_parts.append(f"\nStudent's Code:\n```python\n{context['code']}\n```")

        if "error" in context:
            formatted_parts.append(f"\nError Message:\n{context['error']}")

        if "previous_attempts" in context:
            formatted_parts.append(f"\nPrevious Attempts: {context['previous_attempts']}")

        if "mastery_score" in context:
            formatted_parts.append(f"Current Mastery: {context['mastery_score']}%")

        return "\n".join(formatted_parts)

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on this agent
        """
        try:
            # Test with a simple prompt
            response = await self.invoke_claude(
                user_message="Say 'OK' if you're working.",
                max_tokens=10
            )

            is_healthy = "ok" in response.lower()

            return {
                "agent": self.name,
                "status": "healthy" if is_healthy else "degraded",
                "model": self.model,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Health check failed for {self.name}", error=str(e))
            return {
                "agent": self.name,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
