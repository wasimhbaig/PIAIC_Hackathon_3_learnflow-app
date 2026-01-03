"""
Pytest configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.models.database import Base
from src.api.dependencies import get_db


# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Get authentication headers for testing"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "student@learnflow.com",
            "password": "student123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response"""
    return {
        "content": "This is a test response from the AI agent.",
        "metadata": {
            "confidence": 0.95,
            "agent": "test-agent"
        }
    }


@pytest.fixture
def sample_student():
    """Sample student data"""
    return {
        "student_id": "test-student-123",
        "email": "test@example.com",
        "full_name": "Test Student",
        "current_module": 2,
        "mastery_score": 75
    }


@pytest.fixture
def sample_code_submission():
    """Sample code submission"""
    return {
        "code": "for i in range(5):\n    print(i)",
        "exercise_id": 1,
        "language": "python"
    }
