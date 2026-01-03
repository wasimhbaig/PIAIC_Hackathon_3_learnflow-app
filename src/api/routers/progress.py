"""Progress tracking endpoints"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/{student_id}")
async def get_student_progress(student_id: str):
    """Get comprehensive student progress"""
    return {
        "student_id": student_id,
        "modules": [
            {"module_number": 1, "mastery": 95, "status": "mastered"},
            {"module_number": 2, "mastery": 68, "status": "learning"}
        ],
        "overall_score": 72,
        "streak_days": 5
    }

@router.get("/{student_id}/mastery/{topic_id}")
async def get_topic_mastery(student_id: str, topic_id: int):
    """Get mastery score for specific topic"""
    return {
        "topic_id": topic_id,
        "overall_score": 75,
        "breakdown": {
            "exercise_completion": 80,
            "quiz_score": 75,
            "code_quality": 70,
            "consistency": 65
        }
    }
