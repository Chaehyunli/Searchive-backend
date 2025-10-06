# -*- coding: utf-8 -*-
"""Redis 클라이언트 설정 및 연결 관리"""
import redis.asyncio as aioredis
from src.core.config import settings


# Redis 비동기 클라이언트 인스턴스
redis_client = aioredis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True  # 자동으로 bytes를 str로 디코딩
)


async def get_redis():
    """
    Redis 의존성 주입용 함수
    Usage:
        @router.get("/example")
        async def example(redis: Redis = Depends(get_redis)):
            await redis.set("key", "value")
    """
    return redis_client


async def close_redis():
    """애플리케이션 종료 시 Redis 연결을 닫습니다"""
    await redis_client.close()
