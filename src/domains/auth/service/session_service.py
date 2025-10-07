# -*- coding: utf-8 -*-
"""세션 관리 서비스"""
import json
import uuid
from typing import Dict, Optional
from src.core.redis import redis_client
from src.core.config import settings


class SessionService:
    """Redis를 이용한 세션 관리 서비스 클래스"""

    def __init__(self):
        """SessionService 초기화"""
        self.redis = redis_client
        self.session_expire_time = 3600  # 1시간 (초 단위)

    async def create_session(self, user_id: int) -> str:
        """
        사용자 ID로 새로운 세션을 생성하고 Redis에 저장합니다.

        Args:
            user_id: 사용자 고유 ID

        Returns:
            생성된 세션 ID (UUID)

        Example:
            session_id = await session_service.create_session(user_id=123)
        """
        # 세션 ID 생성
        session_id = str(uuid.uuid4())

        # 세션 데이터 구성
        session_data = {"user_id": user_id}

        # Redis에 저장 (key: "session:{session_id}", value: JSON 문자열)
        await self.redis.setex(
            f"session:{session_id}",
            self.session_expire_time,
            json.dumps(session_data)
        )

        return session_id

    async def get_session(self, session_id: str) -> Optional[Dict]:
        """
        세션 ID로 세션 데이터를 조회합니다.

        Args:
            session_id: 조회할 세션 ID

        Returns:
            세션 데이터 딕셔너리 또는 None (세션이 없는 경우)

        Example:
            session_data = await session_service.get_session(session_id)
            if session_data:
                user_id = session_data.get("user_id")
        """
        session_data_json = await self.redis.get(f"session:{session_id}")

        if not session_data_json:
            return None

        return json.loads(session_data_json)

    async def delete_session(self, session_id: str) -> bool:
        """
        세션 ID로 세션을 삭제합니다 (로그아웃 시 사용).

        Args:
            session_id: 삭제할 세션 ID

        Returns:
            삭제 성공 여부 (True: 성공, False: 세션 없음)

        Example:
            success = await session_service.delete_session(session_id)
        """
        result = await self.redis.delete(f"session:{session_id}")
        return result > 0

    async def extend_session(self, session_id: str) -> bool:
        """
        세션의 만료 시간을 연장합니다.

        Args:
            session_id: 연장할 세션 ID

        Returns:
            연장 성공 여부

        Example:
            success = await session_service.extend_session(session_id)
        """
        result = await self.redis.expire(f"session:{session_id}", self.session_expire_time)
        return result > 0
