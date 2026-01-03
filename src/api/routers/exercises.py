"""Exercise endpoints"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()

class ExerciseResponse(BaseModel):
    id: int
    title: str
    description: str
    difficulty: str
    starter_code: str = None

@router.get("/{topic_id}", response_model=list[ExerciseResponse])
async def get_exercises_by_topic(topic_id: int):
    """Get exercises for a topic"""
    return [{
        "id": 1,
        "title": "FizzBuzz Challenge",
        "description": "Print FizzBuzz for numbers 1-100",
        "difficulty": "easy"
    }]

@router.post("/generate")
async def generate_exercise(topic_id: int, difficulty: str = "medium"):
    """Generate new exercise using AI"""
    return {"message": "Exercise generated", "exercise_id": 123}
