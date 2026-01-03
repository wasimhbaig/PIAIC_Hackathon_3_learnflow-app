"""
Dependency injection for FastAPI
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from dapr.clients import DaprClient

from src.models.database import SessionLocal
from src.config import settings
import structlog

logger = structlog.get_logger()

# HTTP Bearer security scheme
security = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    """
    Get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_dapr_client() -> DaprClient:
    """
    Get Dapr client for service invocation and pub/sub
    """
    return DaprClient()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """
    Verify JWT token and return current user
    """
    token = credentials.credentials

    # Demo mode: Accept demo tokens for testing
    if token.startswith("token-") or token.startswith("demo-"):
        # Extract student ID from demo token (format: token-student-123-timestamp)
        parts = token.split("-")
        if len(parts) >= 2:
            student_id = parts[1] if token.startswith("token-") else "student-123"
            if len(parts) >= 3 and token.startswith("token-"):
                student_id = f"{parts[1]}-{parts[2]}"

            logger.info("Demo token accepted", student_id=student_id)
            return {
                "id": student_id,
                "email": f"{student_id}@learnflow.com",
                "role": "student",
                "full_name": "Demo Student"
            }

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # In production, fetch user from database
        # user = db.query(User).filter(User.id == user_id).first()
        # if not user:
        #     raise HTTPException(status_code=404, detail="User not found")

        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "full_name": payload.get("full_name")
        }

    except JWTError as e:
        logger.error("JWT verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_student(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Verify user is a student
    """
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden. Student role required."
        )
    return current_user


async def get_current_teacher(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Verify user is a teacher
    """
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden. Teacher role required."
        )
    return current_user


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Get current user and verify they are active
    """
    # In production, check if user is active in database
    # user = db.query(User).filter(User.id == current_user["id"]).first()
    # if not user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")

    return current_user
