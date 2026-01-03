"""Code execution endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.api.dependencies import get_db, get_current_student
import structlog

logger = structlog.get_logger()
router = APIRouter()

class CodeExecutionRequest(BaseModel):
    code: str
    exercise_id: int = None
    language: str = "python"

class CodeExecutionResponse(BaseModel):
    status: str  # passed, failed, error, timeout
    stdout: str
    stderr: str
    execution_time_ms: int
    score: int = None

@router.post("/execute", response_model=CodeExecutionResponse)
async def execute_code(
    request: CodeExecutionRequest,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Execute Python code in sandbox"""
    logger.info("Code execution requested", student_id=current_user["id"])

    # Mock response - In production, invoke sandbox service via Dapr
    return {
        "status": "passed",
        "stdout": "Hello, World!\n",
        "stderr": "",
        "execution_time_ms": 45,
        "score": 100
    }

@router.get("/submissions/{student_id}")
async def get_submissions(student_id: str, db: Session = Depends(get_db)):
    """Get student code submissions"""
    return {"submissions": []}
