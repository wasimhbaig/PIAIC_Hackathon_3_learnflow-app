"""Student endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.api.dependencies import get_db, get_current_student

router = APIRouter()

@router.get("/me")
async def get_current_student_profile(current_user: dict = Depends(get_current_student)):
    """Get current student profile"""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "current_module": 2,
        "learning_pace": "normal"
    }

@router.get("/{student_id}")
async def get_student(student_id: str, db: Session = Depends(get_db)):
    """Get student by ID"""
    return {"id": student_id, "full_name": "Maya Student"}

@router.get("/{student_id}/dashboard")
async def get_student_dashboard(student_id: str):
    """Get student dashboard data"""
    return {
        "current_module": {"number": 2, "name": "Control Flow", "progress": 68},
        "recent_activity": [],
        "upcoming_quizzes": []
    }
