"""
Authentication endpoints
Handles user registration, login, and token management
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from jose import jwt
from passlib.context import CryptContext

from src.api.dependencies import get_db
from src.config import settings
import structlog

logger = structlog.get_logger()

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Request/Response models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str  # "student" or "teacher"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user (student or teacher)

    - **email**: Valid email address
    - **password**: Strong password (min 8 characters)
    - **full_name**: User's full name
    - **role**: Either "student" or "teacher"
    """
    # Validate role
    if user.role not in ["student", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be either 'student' or 'teacher'"
        )

    # Check password strength
    if len(user.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )

    # In production: Check if email already exists
    # existing_user = db.query(User).filter(User.email == user.email).first()
    # if existing_user:
    #     raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    hashed_password = get_password_hash(user.password)

    # In production: Create user in database
    # new_user = User(
    #     email=user.email,
    #     hashed_password=hashed_password,
    #     full_name=user.full_name,
    #     role=user.role
    # )
    # db.add(new_user)
    # db.commit()
    # db.refresh(new_user)

    # For MVP: Mock user ID
    user_id = "mock-user-id-123"

    logger.info(
        "User registered successfully",
        email=user.email,
        role=user.role
    )

    # Create access token
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user_id,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/login", response_model=Token)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """
    Login and get access token

    - **email**: Registered email address
    - **password**: User password

    Returns JWT access token for subsequent API calls
    """
    # In production: Fetch user from database
    # db_user = db.query(User).filter(User.email == user.email).first()
    # if not db_user or not verify_password(user.password, db_user.hashed_password):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Incorrect email or password",
    #         headers={"WWW-Authenticate": "Bearer"}
    #     )

    # For MVP: Mock authentication
    # In production, verify against database
    mock_users = {
        "student@learnflow.com": {
            "id": "student-123",
            "password_hash": get_password_hash("student123"),
            "role": "student",
            "full_name": "Maya Student"
        },
        "teacher@learnflow.com": {
            "id": "teacher-456",
            "password_hash": get_password_hash("teacher123"),
            "role": "teacher",
            "full_name": "Mr. Rodriguez"
        }
    }

    mock_user = mock_users.get(user.email)
    if not mock_user or not verify_password(user.password, mock_user["password_hash"]):
        logger.warning("Failed login attempt", email=user.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    logger.info("User logged in successfully", email=user.email, role=mock_user["role"])

    # Create access token
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": mock_user["id"],
            "email": user.email,
            "role": mock_user["role"],
            "full_name": mock_user["full_name"]
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/token", response_model=Token)
async def login_oauth(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login
    Used by Swagger UI and other OAuth2 clients
    """
    # Reuse login logic
    user_login = UserLogin(email=form_data.username, password=form_data.password)
    return await login(user_login, db)


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token
    (Not implemented in MVP)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh not implemented in MVP"
    )


@router.post("/logout")
async def logout():
    """
    Logout (invalidate token)
    In production, would add token to blacklist
    """
    logger.info("User logged out")
    return {"message": "Logged out successfully"}
