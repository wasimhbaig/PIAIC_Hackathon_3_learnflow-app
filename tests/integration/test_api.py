"""
Integration tests for API endpoints
"""
import pytest
from fastapi import status


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_register_student(self, client):
        """Test student registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newstudent@test.com",
                "password": "password123",
                "full_name": "New Student",
                "role": "student"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert "access_token" in response.json()

    def test_register_invalid_role(self, client):
        """Test registration with invalid role"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@test.com",
                "password": "password123",
                "full_name": "Test User",
                "role": "admin"  # Invalid role
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_success(self, client):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "student@learnflow.com",
                "password": "student123"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "student@learnflow.com",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["service"] == "LearnFlow API Gateway"

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"

    def test_liveness_probe(self, client):
        """Test liveness probe"""
        response = client.get("/health/live")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "alive"

    def test_startup_probe(self, client):
        """Test startup probe"""
        response = client.get("/health/startup")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "started"


class TestStudentEndpoints:
    """Test student endpoints"""

    def test_get_current_student_profile(self, client, auth_headers):
        """Test getting current student profile"""
        response = client.get(
            "/api/v1/students/me",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "email" in data
        assert "current_module" in data

    def test_get_student_dashboard(self, client, auth_headers):
        """Test getting student dashboard"""
        response = client.get(
            "/api/v1/students/student-123/dashboard",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "current_module" in data


class TestCodeEndpoints:
    """Test code execution endpoints"""

    def test_execute_code_success(self, client, auth_headers):
        """Test successful code execution"""
        response = client.post(
            "/api/v1/code/execute",
            headers=auth_headers,
            json={
                "code": "print('Hello, World!')",
                "language": "python"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "passed"
        assert "stdout" in data


class TestProgressEndpoints:
    """Test progress tracking endpoints"""

    def test_get_student_progress(self, client, auth_headers):
        """Test getting student progress"""
        response = client.get(
            "/api/v1/progress/student-123",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "modules" in data
        assert "overall_score" in data

    def test_get_topic_mastery(self, client, auth_headers):
        """Test getting topic mastery"""
        response = client.get(
            "/api/v1/progress/student-123/mastery/1",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "overall_score" in data
        assert "breakdown" in data


class TestExerciseEndpoints:
    """Test exercise endpoints"""

    def test_get_exercises_by_topic(self, client, auth_headers):
        """Test getting exercises for a topic"""
        response = client.get(
            "/api/v1/exercises/1",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_generate_exercise(self, client, auth_headers):
        """Test exercise generation"""
        response = client.post(
            "/api/v1/exercises/generate?topic_id=1&difficulty=easy",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "exercise_id" in data or "message" in data
