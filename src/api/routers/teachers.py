"""Teacher endpoints"""
from fastapi import APIRouter, Depends
from src.api.dependencies import get_current_teacher

router = APIRouter()

@router.get("/me")
async def get_teacher_profile(current_user: dict = Depends(get_current_teacher)):
    """Get teacher profile"""
    return {"id": current_user["id"], "full_name": current_user["full_name"]}

@router.get("/classes/{class_id}/performance")
async def get_class_performance(class_id: int):
    """Get class performance metrics"""
    return {
        "class_id": class_id,
        "total_students": 25,
        "avg_mastery": 72.5,
        "struggle_alerts": 3
    }

@router.get("/struggle-alerts")
async def get_struggle_alerts(current_user: dict = Depends(get_current_teacher)):
    """Get active struggle alerts"""
    return {"alerts": []}
