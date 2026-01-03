"""
Unit tests for business logic services
"""
import pytest
from datetime import datetime

from src.services.mastery_service import MasteryService
from src.services.struggle_detection import StruggleDetectionService


class TestMasteryService:
    """Test Mastery Calculation Service"""

    @pytest.fixture
    def service(self):
        return MasteryService()

    def test_calculate_mastery_beginner(self, service):
        """Test mastery calculation for beginner level"""
        result = service.calculate_mastery(
            exercise_completion_score=30,
            quiz_score=25,
            code_quality_score=20,
            consistency_score=15
        )

        assert result["overall_score"] == pytest.approx(25.5, rel=0.1)
        assert result["mastery_level"] == "beginner"

    def test_calculate_mastery_learning(self, service):
        """Test mastery calculation for learning level"""
        result = service.calculate_mastery(
            exercise_completion_score=60,
            quiz_score=65,
            code_quality_score=55,
            consistency_score=50
        )

        assert 41 <= result["overall_score"] <= 70
        assert result["mastery_level"] == "learning"

    def test_calculate_mastery_proficient(self, service):
        """Test mastery calculation for proficient level"""
        result = service.calculate_mastery(
            exercise_completion_score=80,
            quiz_score=85,
            code_quality_score=75,
            consistency_score=70
        )

        assert 71 <= result["overall_score"] <= 90
        assert result["mastery_level"] == "proficient"

    def test_calculate_mastery_mastered(self, service):
        """Test mastery calculation for mastered level"""
        result = service.calculate_mastery(
            exercise_completion_score=95,
            quiz_score=98,
            code_quality_score=92,
            consistency_score=100
        )

        assert result["overall_score"] >= 91
        assert result["mastery_level"] == "mastered"

    def test_weighted_formula(self, service):
        """Test weighted formula calculation"""
        # Exercise completion: 40%, Quiz: 30%, Quality: 20%, Consistency: 10%
        result = service.calculate_mastery(
            exercise_completion_score=100,  # 40 points
            quiz_score=100,                 # 30 points
            code_quality_score=100,         # 20 points
            consistency_score=100           # 10 points
        )

        assert result["overall_score"] == 100.0

    def test_exercise_completion_calculation(self, service):
        """Test exercise completion score calculation"""
        score = service.calculate_exercise_completion(completed=8, total=10)
        assert score == 80.0

    def test_consistency_score_7_days(self, service):
        """Test consistency score for 7+ day streak"""
        score = service.calculate_consistency_score(current_streak=7)
        assert score == 100.0

    def test_consistency_score_5_days(self, service):
        """Test consistency score for 5-6 day streak"""
        score = service.calculate_consistency_score(current_streak=5)
        assert score == 80.0

    def test_consistency_score_no_streak(self, service):
        """Test consistency score for no streak"""
        score = service.calculate_consistency_score(current_streak=0)
        assert score == 0.0


class TestStruggleDetectionService:
    """Test Struggle Detection Service"""

    @pytest.fixture
    def service(self):
        return StruggleDetectionService()

    def test_detect_repeated_errors(self, service):
        """Test detection of repeated errors"""
        activity = [
            {"event_type": "code_execution_failed", "error_type": "NameError"},
            {"event_type": "code_execution_failed", "error_type": "NameError"},
            {"event_type": "code_execution_failed", "error_type": "NameError"},
        ]

        struggles = service.detect_struggles("student-123", activity)

        assert len(struggles) > 0
        assert any(s["type"] == "repeated_error" for s in struggles)

    def test_detect_stuck_on_exercise(self, service):
        """Test detection of stuck on exercise"""
        base_time = datetime.utcnow().isoformat()

        activity = [
            {
                "event_type": "exercise_started",
                "exercise_id": 42,
                "timestamp": "2025-01-02T10:00:00Z"
            },
            {
                "event_type": "exercise_attempt",
                "exercise_id": 42,
                "timestamp": "2025-01-02T10:15:00Z"  # 15 minutes later
            }
        ]

        struggles = service.detect_struggles("student-123", activity)

        # Should detect stuck on exercise (> 10 minutes)
        assert any(s["type"] == "stuck_on_exercise" for s in struggles)

    def test_detect_low_quiz_score(self, service):
        """Test detection of low quiz score"""
        activity = [
            {
                "event_type": "quiz_completed",
                "quiz_id": 1,
                "score_percentage": 40,  # Below 50% threshold
                "topic_id": 5
            }
        ]

        struggles = service.detect_struggles("student-123", activity)

        assert any(s["type"] == "low_quiz_score" for s in struggles)

    def test_detect_confusion_signals(self, service):
        """Test detection of confusion signals"""
        activity = [
            {
                "event_type": "chat_message",
                "message": "I don't understand this concept"
            },
            {
                "event_type": "chat_message",
                "message": "I'm stuck on this problem"
            }
        ]

        struggles = service.detect_struggles("student-123", activity)

        assert any(s["type"] == "confusion_signal" for s in struggles)

    def test_detect_multiple_failures(self, service):
        """Test detection of multiple consecutive failures"""
        activity = [
            {"event_type": "code_execution_failed"},
            {"event_type": "code_execution_failed"},
            {"event_type": "code_execution_failed"},
            {"event_type": "code_execution_failed"},
            {"event_type": "code_execution_failed"},
        ]

        struggles = service.detect_struggles("student-123", activity)

        assert any(s["type"] == "multiple_failures" for s in struggles)

    def test_no_struggles_detected(self, service):
        """Test when no struggles are detected"""
        activity = [
            {"event_type": "code_execution_passed"},
            {"event_type": "quiz_completed", "score_percentage": 85},
        ]

        struggles = service.detect_struggles("student-123", activity)

        assert len(struggles) == 0

    def test_create_struggle_alert(self, service):
        """Test struggle alert creation"""
        struggle = {
            "type": "repeated_error",
            "severity": "medium",
            "details": {"error_type": "NameError", "count": 3},
            "recommendation": "Send Debug Agent"
        }

        alert = service.create_struggle_alert(
            student_id="student-123",
            topic_id=5,
            struggle=struggle
        )

        assert alert["student_id"] == "student-123"
        assert alert["topic_id"] == 5
        assert alert["trigger_type"] == "repeated_error"
        assert alert["severity"] == "medium"
        assert not alert["is_resolved"]
        assert "created_at" in alert
