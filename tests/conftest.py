import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import redis

from src.core.config import settings
from src.db.session import Base


# ============================================
# Pytest Configuration
# ============================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================
# Database Fixtures
# ============================================

@pytest.fixture(scope="session")
def db_engine():
    """Create a test database engine."""
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=StaticPool,
    )
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a new database session for a test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def db_session_with_data(db_session) -> Generator[Session, None, None]:
    """Create a database session with test data."""
    # Add any common test data here
    yield db_session


# ============================================
# Redis Fixtures
# ============================================

@pytest.fixture(scope="session")
def redis_client():
    """Create a Redis client for testing."""
    client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
        db=1,  # Use database 1 for testing (not production db 0)
        decode_responses=True
    )
    yield client
    # Clean up test data
    client.flushdb()
    client.close()


@pytest.fixture(scope="function")
def clean_redis(redis_client):
    """Clean Redis before each test."""
    redis_client.flushdb()
    yield redis_client
    redis_client.flushdb()


# ============================================
# FastAPI App Fixtures
# ============================================

@pytest.fixture(scope="session")
def app():
    """Create a FastAPI app instance for testing."""
    from src.main import app
    return app


@pytest.fixture(scope="function")
async def async_client(app):
    """Create an async HTTP client for testing."""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
