from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from src.core.config import settings

# SQLAlchemy 모델용 Base 클래스
Base = declarative_base()

# 동기 엔진 (Alembic 마이그레이션용)
sync_engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# 동기 SessionLocal (마이그레이션용)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)

# 비동기 엔진 (FastAPI 런타임용)
async_engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    future=True,
)

# 비동기 SessionLocal (FastAPI 의존성 주입용)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db():
    """
    비동기 데이터베이스 세션을 가져오는 의존성 함수
    FastAPI 라우트 사용 예시:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_db():
    """
    동기 데이터베이스 세션을 가져오는 의존성 함수 (드물게 사용)
    주로 Alembic이나 특수한 경우에 사용
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
