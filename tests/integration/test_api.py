"""Integration tests for API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from uuid import UUID

# Эти тесты требуют запущенного приложения с тестовой БД
# Запуск: pytest tests/integration/test_api.py -v


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    from src.main import app
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint returns API info."""
    from src.main import app
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "PDF Converter Bot API" in data["service"]
        assert "docs" in data


@pytest.mark.asyncio
async def test_register_user():
    """Test user registration."""
    from src.main import app
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        # Первый запрос должен быть успешным
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email():
    """Test registration with duplicate email fails."""
    from src.main import app
    
    # Сначала регистрируем пользователя
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "testpassword123"
            }
        )
        
        # Попытка регистрации с тем же email
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "anotherpassword"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success():
    """Test successful login."""
    from src.main import app
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Регистрируем пользователя
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "testpassword123"
            }
        )
        
        # Логинимся
        response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "login@example.com",
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    from src.main import app
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "nonexistent@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
