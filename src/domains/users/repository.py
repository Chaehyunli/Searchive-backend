# -*- coding: utf-8 -*-
"""User 도메인 Repository"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domains.users.models import User


class UserRepository:
    """User 엔티티 데이터 접근 계층"""

    def __init__(self, db: AsyncSession):
        """
        UserRepository 초기화

        Args:
            db: SQLAlchemy AsyncSession
        """
        self.db = db

    async def find_by_kakao_id(self, kakao_id: str) -> Optional[User]:
        """
        카카오 ID로 사용자 조회

        Args:
            kakao_id: 카카오 소셜 ID

        Returns:
            User 객체 또는 None
        """
        result = await self.db.execute(
            select(User).where(User.kakao_id == kakao_id)
        )
        return result.scalar_one_or_none()

    async def find_by_user_id(self, user_id: int) -> Optional[User]:
        """
        사용자 ID로 사용자 조회

        Args:
            user_id: 사용자 고유 ID

        Returns:
            User 객체 또는 None
        """
        result = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, kakao_id: str, nickname: str) -> User:
        """
        신규 사용자 생성

        Args:
            kakao_id: 카카오 소셜 ID
            nickname: 사용자 닉네임

        Returns:
            생성된 User 객체
        """
        user = User(
            kakao_id=kakao_id,
            nickname=nickname
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_nickname(self, user_id: int, nickname: str) -> Optional[User]:
        """
        사용자 닉네임 업데이트

        Args:
            user_id: 사용자 고유 ID
            nickname: 새로운 닉네임

        Returns:
            업데이트된 User 객체 또는 None (사용자 없을 경우)
        """
        user = await self.find_by_user_id(user_id)
        if not user:
            return None

        user.nickname = nickname
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user_id: int) -> bool:
        """
        사용자 삭제

        Args:
            user_id: 사용자 고유 ID

        Returns:
            삭제 성공 여부
        """
        user = await self.find_by_user_id(user_id)
        if not user:
            return False

        await self.db.delete(user)
        await self.db.commit()
        return True
