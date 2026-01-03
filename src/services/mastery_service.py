"""
Mastery Calculation Service
Calculates and updates student mastery scores
"""
from typing import Dict
import structlog
from src.config import settings

logger = structlog.get_logger()


class MasteryService:
    """
    Calculate topic mastery scores using weighted formula

    Formula:
    - Exercise Completion: 40%
    - Quiz Score: 30%
    - Code Quality: 20%
    - Consistency (Streak): 10%
    """

    def __init__(self):
        self.weights = settings.mastery_weights

    def calculate_mastery(
        self,
        exercise_completion_score: float,
        quiz_score: float,
        code_quality_score: float,
        consistency_score: float
    ) -> Dict[str, any]:
        """
        Calculate overall mastery score and level

        Args:
            exercise_completion_score: 0-100
            quiz_score: 0-100
            code_quality_score: 0-100
            consistency_score: 0-100

        Returns:
            Dict with overall_score and mastery_level
        """
        # Calculate weighted average
        overall_score = (
            exercise_completion_score * self.weights["exercise_completion"] +
            quiz_score * self.weights["quiz_score"] +
            code_quality_score * self.weights["code_quality"] +
            consistency_score * self.weights["consistency"]
        )

        # Determine mastery level
        mastery_level = self._get_mastery_level(overall_score)

        logger.debug(
            "Mastery calculated",
            overall_score=round(overall_score, 1),
            level=mastery_level,
            components={
                "exercise": exercise_completion_score,
                "quiz": quiz_score,
                "quality": code_quality_score,
                "consistency": consistency_score
            }
        )

        return {
            "overall_score": round(overall_score, 1),
            "mastery_level": mastery_level,
            "components": {
                "exercise_completion": exercise_completion_score,
                "quiz_score": quiz_score,
                "code_quality": code_quality_score,
                "consistency": consistency_score
            }
        }

    def _get_mastery_level(self, score: float) -> str:
        """Map score to mastery level"""
        if score < 41:
            return "beginner"
        elif score < 71:
            return "learning"
        elif score < 91:
            return "proficient"
        else:
            return "mastered"

    def calculate_exercise_completion(self, completed: int, total: int) -> float:
        """Calculate exercise completion score"""
        if total == 0:
            return 0.0
        return (completed / total) * 100

    def calculate_consistency_score(self, current_streak: int) -> float:
        """
        Calculate consistency score based on streak

        7+ days = 100
        5-6 days = 80
        3-4 days = 60
        1-2 days = 40
        0 days = 0
        """
        if current_streak >= 7:
            return 100.0
        elif current_streak >= 5:
            return 80.0
        elif current_streak >= 3:
            return 60.0
        elif current_streak >= 1:
            return 40.0
        else:
            return 0.0
