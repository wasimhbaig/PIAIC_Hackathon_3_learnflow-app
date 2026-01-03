"""Code execution endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.api.dependencies import get_db, get_current_student
import structlog
import subprocess
import time
import sys
from io import StringIO
import contextlib

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

    start_time = time.time()
    stdout_output = ""
    stderr_output = ""
    status = "passed"

    try:
        # Capture stdout and stderr
        stdout_capture = StringIO()
        stderr_capture = StringIO()

        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            try:
                # Execute the code
                exec(request.code, {"__builtins__": __builtins__})
            except Exception as e:
                stderr_capture.write(f"{type(e).__name__}: {str(e)}")
                status = "error"

        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()

        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)

        # If there were errors, mark as failed
        if stderr_output:
            status = "error"

        logger.info("Code execution completed",
                   student_id=current_user["id"],
                   status=status,
                   execution_time_ms=execution_time_ms)

        return {
            "status": status,
            "stdout": stdout_output,
            "stderr": stderr_output,
            "execution_time_ms": execution_time_ms,
            "score": 100 if status == "passed" else 0
        }

    except Exception as e:
        logger.error("Code execution failed", error=str(e), student_id=current_user["id"])
        return {
            "status": "error",
            "stdout": "",
            "stderr": f"Execution error: {str(e)}",
            "execution_time_ms": int((time.time() - start_time) * 1000),
            "score": 0
        }

@router.get("/submissions/{student_id}")
async def get_submissions(student_id: str, db: Session = Depends(get_db)):
    """Get student code submissions"""
    return {"submissions": []}
