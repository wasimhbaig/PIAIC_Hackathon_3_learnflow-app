"""
Unit tests for AI agents
"""
import pytest
from unittest.mock import AsyncMock, patch

from src.agents.triage import TriageAgent
from src.agents.concepts import ConceptsAgent
from src.agents.code_review import CodeReviewAgent
from src.agents.debug import DebugAgent
from src.agents.exercise import ExerciseAgent
from src.agents.progress import ProgressAgent


class TestTriageAgent:
    """Test Triage Agent routing logic"""

    @pytest.fixture
    def agent(self):
        return TriageAgent()

    @pytest.mark.asyncio
    async def test_route_to_concepts(self, agent):
        """Test routing to Concepts Agent"""
        result = await agent.process(
            message="How do for loops work?",
            context={}
        )

        assert result["target_agent"] == "concepts"
        assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_route_to_debug(self, agent):
        """Test routing to Debug Agent"""
        result = await agent.process(
            message="I'm getting a NameError in my code",
            context={}
        )

        assert result["target_agent"] == "debug"

    @pytest.mark.asyncio
    async def test_route_to_code_review(self, agent):
        """Test routing to Code Review Agent"""
        result = await agent.process(
            message="Can you review my function?",
            context={}
        )

        assert result["target_agent"] == "code-review"

    @pytest.mark.asyncio
    async def test_route_to_exercise(self, agent):
        """Test routing to Exercise Agent"""
        result = await agent.process(
            message="Give me a practice problem",
            context={}
        )

        assert result["target_agent"] == "exercise"

    @pytest.mark.asyncio
    async def test_route_to_progress(self, agent):
        """Test routing to Progress Agent"""
        result = await agent.process(
            message="How am I doing?",
            context={}
        )

        assert result["target_agent"] == "progress"


class TestConceptsAgent:
    """Test Concepts Agent"""

    @pytest.fixture
    def agent(self):
        return ConceptsAgent()

    def test_initialization(self, agent):
        """Test agent initialization"""
        assert agent.name == "concepts"
        assert agent.purpose == "Explain Python concepts with examples and adaptive teaching"

    def test_system_prompt(self, agent):
        """Test system prompt generation"""
        prompt = agent.get_system_prompt()

        assert "Concepts Agent" in prompt
        assert "student level" in prompt.lower()
        assert "code example" in prompt.lower()


class TestCodeReviewAgent:
    """Test Code Review Agent"""

    @pytest.fixture
    def agent(self):
        return CodeReviewAgent()

    def test_initialization(self, agent):
        """Test agent initialization"""
        assert agent.name == "code-review"

    def test_system_prompt_contains_criteria(self, agent):
        """Test system prompt includes review criteria"""
        prompt = agent.get_system_prompt()

        assert "Correctness" in prompt
        assert "Style" in prompt
        assert "Efficiency" in prompt
        assert "Readability" in prompt
        assert "PEP 8" in prompt


class TestDebugAgent:
    """Test Debug Agent"""

    @pytest.fixture
    def agent(self):
        return DebugAgent()

    def test_initialization(self, agent):
        """Test agent initialization"""
        assert agent.name == "debug"

    def test_system_prompt_encourages_hints(self, agent):
        """Test system prompt emphasizes hints over solutions"""
        prompt = agent.get_system_prompt()

        assert "hints" in prompt.lower()
        assert "guide" in prompt.lower()
        # Should NOT give full solutions
        assert "never write the corrected code" in prompt.lower()


class TestExerciseAgent:
    """Test Exercise Agent"""

    @pytest.fixture
    def agent(self):
        return ExerciseAgent()

    def test_initialization(self, agent):
        """Test agent initialization"""
        assert agent.name == "exercise"

    def test_system_prompt_includes_exercise_format(self, agent):
        """Test system prompt includes exercise format"""
        prompt = agent.get_system_prompt()

        assert "test cases" in prompt.lower()
        assert "hints" in prompt.lower()
        assert "difficulty" in prompt.lower()


class TestProgressAgent:
    """Test Progress Agent"""

    @pytest.fixture
    def agent(self):
        return ProgressAgent()

    def test_initialization(self, agent):
        """Test agent initialization"""
        assert agent.name == "progress"

    def test_mastery_level_mapping(self, agent):
        """Test mastery score to level mapping"""
        assert agent._get_mastery_level(30) == "Beginner 🔴"
        assert agent._get_mastery_level(60) == "Learning 🟡"
        assert agent._get_mastery_level(85) == "Proficient 🟢"
        assert agent._get_mastery_level(95) == "Mastered 🔵"

    def test_system_prompt_includes_mastery_levels(self, agent):
        """Test system prompt includes mastery levels"""
        prompt = agent.get_system_prompt()

        assert "Beginner" in prompt
        assert "Learning" in prompt
        assert "Proficient" in prompt
        assert "Mastered" in prompt
