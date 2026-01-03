"""
Struggle Detection Service
Identifies students who need help and triggers alerts
"""
from typing import Dict, List, Optional
import structlog
from datetime import datetime, timedelta
from src.config import settings

logger = structlog.get_logger()


class StruggleDetectionService:
    """
    Detect struggling students based on activity patterns

    Triggers:
    - Same error type 3+ times
    - Stuck on exercise > 10 minutes
    - Quiz score < 50%
    - Confusion signals ("I don't understand", "I'm stuck")
    - 5+ failed code executions in a row
    """

    def __init__(self):
        self.thresholds = settings.struggle_thresholds

    def detect_struggles(
        self,
        student_id: str,
        recent_activity: List[Dict]
    ) -> List[Dict]:
        """
        Analyze recent activity and detect struggle patterns

        Args:
            student_id: Student UUID
            recent_activity: List of activity events

        Returns:
            List of detected struggles with recommendations
        """
        struggles = []

        # Check for repeated errors
        repeated_errors = self._check_repeated_errors(recent_activity)
        if repeated_errors:
            struggles.append({
                "type": "repeated_error",
                "severity": "medium",
                "details": repeated_errors,
                "recommendation": "Send Debug Agent with targeted hints"
            })

        # Check if stuck on exercise
        stuck_exercise = self._check_stuck_on_exercise(recent_activity)
        if stuck_exercise:
            struggles.append({
                "type": "stuck_on_exercise",
                "severity": "high",
                "details": stuck_exercise,
                "recommendation": "Provide progressive hints or easier exercise"
            })

        # Check quiz performance
        low_quiz = self._check_low_quiz_score(recent_activity)
        if low_quiz:
            struggles.append({
                "type": "low_quiz_score",
                "severity": "high",
                "details": low_quiz,
                "recommendation": "Review topic concepts with Concepts Agent"
            })

        # Check for confusion signals
        confusion = self._check_confusion_signals(recent_activity)
        if confusion:
            struggles.append({
                "type": "confusion_signal",
                "severity": "medium",
                "details": confusion,
                "recommendation": "Proactive intervention by appropriate agent"
            })

        # Check for multiple failures
        failures = self._check_multiple_failures(recent_activity)
        if failures:
            struggles.append({
                "type": "multiple_failures",
                "severity": "high",
                "details": failures,
                "recommendation": "Simplify exercise or provide worked example"
            })

        if struggles:
            logger.warning(
                "Student struggles detected",
                student_id=student_id,
                struggle_count=len(struggles),
                types=[s["type"] for s in struggles]
            )

        return struggles

    def _check_repeated_errors(self, activity: List[Dict]) -> Optional[Dict]:
        """Check for same error type appearing 3+ times"""
        error_counts = {}

        for event in activity:
            if event.get("event_type") == "code_execution_failed":
                error_type = event.get("error_type", "unknown")
                error_counts[error_type] = error_counts.get(error_type, 0) + 1

        for error_type, count in error_counts.items():
            if count >= self.thresholds["repeated_error_count"]:
                return {
                    "error_type": error_type,
                    "count": count,
                    "threshold": self.thresholds["repeated_error_count"]
                }

        return None

    def _check_stuck_on_exercise(self, activity: List[Dict]) -> Optional[Dict]:
        """Check if student stuck on same exercise > 10 minutes"""
        exercise_times = {}

        for event in activity:
            if event.get("event_type") in ["exercise_started", "exercise_attempt"]:
                exercise_id = event.get("exercise_id")
                timestamp = datetime.fromisoformat(event.get("timestamp"))

                if exercise_id not in exercise_times:
                    exercise_times[exercise_id] = {
                        "start": timestamp,
                        "last_attempt": timestamp,
                        "attempts": 0
                    }
                else:
                    exercise_times[exercise_id]["last_attempt"] = timestamp
                    exercise_times[exercise_id]["attempts"] += 1

        # Check time spent
        for exercise_id, times in exercise_times.items():
            duration = (times["last_attempt"] - times["start"]).total_seconds() / 60

            if duration > self.thresholds["stuck_minutes"]:
                return {
                    "exercise_id": exercise_id,
                    "time_spent_minutes": round(duration, 1),
                    "attempts": times["attempts"],
                    "threshold_minutes": self.thresholds["stuck_minutes"]
                }

        return None

    def _check_low_quiz_score(self, activity: List[Dict]) -> Optional[Dict]:
        """Check for quiz scores below 50%"""
        for event in activity:
            if event.get("event_type") == "quiz_completed":
                score = event.get("score_percentage", 100)

                if score < self.thresholds["quiz_threshold_percent"]:
                    return {
                        "quiz_id": event.get("quiz_id"),
                        "score": score,
                        "threshold": self.thresholds["quiz_threshold_percent"],
                        "topic_id": event.get("topic_id")
                    }

        return None

    def _check_confusion_signals(self, activity: List[Dict]) -> Optional[Dict]:
        """Check for confusion phrases in chat messages"""
        confusion_count = 0
        confusion_messages = []

        for event in activity:
            if event.get("event_type") == "chat_message":
                message = event.get("message", "").lower()

                for signal in self.thresholds["confusion_signals"]:
                    if signal.lower() in message:
                        confusion_count += 1
                        confusion_messages.append({
                            "signal": signal,
                            "message": message[:100]
                        })
                        break

        if confusion_count >= 2:
            return {
                "count": confusion_count,
                "signals": confusion_messages
            }

        return None

    def _check_multiple_failures(self, activity: List[Dict]) -> Optional[Dict]:
        """Check for 5+ consecutive failed executions"""
        consecutive_failures = 0
        max_consecutive = 0

        for event in activity:
            if event.get("event_type") == "code_execution_failed":
                consecutive_failures += 1
                max_consecutive = max(max_consecutive, consecutive_failures)
            elif event.get("event_type") == "code_execution_passed":
                consecutive_failures = 0

        if max_consecutive >= self.thresholds["failed_executions"]:
            return {
                "consecutive_failures": max_consecutive,
                "threshold": self.thresholds["failed_executions"]
            }

        return None

    def create_struggle_alert(
        self,
        student_id: str,
        topic_id: int,
        struggle: Dict
    ) -> Dict:
        """
        Create a struggle alert for teacher notification

        Args:
            student_id: Student UUID
            topic_id: Topic ID where struggle occurred
            struggle: Struggle details from detect_struggles()

        Returns:
            Formatted alert for database/Kafka
        """
        alert = {
            "student_id": student_id,
            "topic_id": topic_id,
            "trigger_type": struggle["type"],
            "severity": struggle["severity"],
            "description": self._format_struggle_description(struggle),
            "suggested_action": struggle["recommendation"],
            "is_resolved": False,
            "created_at": datetime.utcnow().isoformat()
        }

        logger.info(
            "Struggle alert created",
            student_id=student_id,
            type=struggle["type"],
            severity=struggle["severity"]
        )

        return alert

    def _format_struggle_description(self, struggle: Dict) -> str:
        """Format struggle details into readable description"""
        struggle_type = struggle["type"]
        details = struggle["details"]

        if struggle_type == "repeated_error":
            return f"Student encountered {details['error_type']} {details['count']} times"

        elif struggle_type == "stuck_on_exercise":
            return f"Student spent {details['time_spent_minutes']} minutes on exercise {details['exercise_id']}"

        elif struggle_type == "low_quiz_score":
            return f"Student scored {details['score']}% on quiz (below {details['threshold']}%)"

        elif struggle_type == "confusion_signal":
            return f"Student expressed confusion {details['count']} times"

        elif struggle_type == "multiple_failures":
            return f"Student had {details['consecutive_failures']} consecutive code execution failures"

        return "Student appears to be struggling"
