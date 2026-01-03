"""Quiz endpoints"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class QuizSubmission(BaseModel):
    quiz_id: int
    answers: dict

@router.get("/{topic_id}")
async def get_quiz(topic_id: int):
    """Get quiz for topic"""
    return {"questions": [], "total_points": 50}

@router.post("/submit")
async def submit_quiz(submission: QuizSubmission):
    """Submit quiz answers"""
    return {"score": 80, "passed": True}
