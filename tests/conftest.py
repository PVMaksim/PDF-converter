"""
Pytest fixtures for integration tests.
"""
import asyncio
import pytest
from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base, get_db
from src.config import Settings


# Тестовые настройки
@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Create test settings with in-memory SQLite for speed."""
    import os
    
    os.environ['SECRET_KEY'] = 'test-secret-key-for-testing'
    os.environ['TELEGRAM_BOT_TOKEN'] = 'test-token'
    os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'
    os.environ['DEBUG'] = 'true'
    
    from src.config import Settings
    return Settings()


@pytest.fixture(scope="function")
async def test_engine(test_settings: Settings):
    """Create test database engine."""
    engine = create_async_engine(
        test_settings.DATABASE_URL,
        echo=True,
        poolclass=StaticPool,
    )
    
    # Создаём все таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Удаляем все таблицы после теста
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def override_get_db(test_session: AsyncSession):
    """Override get_db dependency for testing."""
    async def _get_db():
        yield test_session
    
    return _get_db


@pytest.fixture
def anyio_backend():
    """AnyIO backend for async tests."""
    return "asyncio"
