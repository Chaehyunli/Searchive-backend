# -*- coding: utf-8 -*-
"""Tag 도메인 Service"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.domains.tags.repository import TagRepository, DocumentTagRepository
from src.domains.tags.models import Tag
import logging

logger = logging.getLogger(__name__)


class TagService:
    """Tag 비즈니스 로직 처리 계층"""

    def __init__(self, db: AsyncSession):
        """
        TagService 초기화

        Args:
            db: SQLAlchemy AsyncSession
        """
        self.tag_repository = TagRepository(db)
        self.document_tag_repository = DocumentTagRepository(db)

    async def get_or_create_tag(self, name: str) -> Tag:
        """
        태그 조회 또는 생성

        Args:
            name: 태그 이름

        Returns:
            Tag 객체
        """
        return await self.tag_repository.get_or_create(name)

    async def get_or_create_tags(self, names: List[str]) -> List[Tag]:
        """
        여러 태그를 한 번에 조회 또는 생성 (N+1 문제 방지)

        Args:
            names: 태그 이름 리스트

        Returns:
            Tag 객체 리스트
        """
        if not names:
            return []

        # 중복 제거 및 정규화
        unique_names = list(set(name.strip().lower() for name in names if name.strip()))

        logger.info(f"태그 조회/생성 시작: {unique_names}")
        tags = await self.tag_repository.bulk_get_or_create(unique_names)
        logger.info(f"태그 조회/생성 완료: {len(tags)}개")

        return tags

    async def attach_tags_to_document(
        self,
        document_id: int,
        tag_names: List[str]
    ) -> List[Tag]:
        """
        문서에 태그 연결

        Args:
            document_id: 문서 ID
            tag_names: 태그 이름 리스트

        Returns:
            연결된 Tag 객체 리스트
        """
        if not tag_names:
            logger.info(f"문서 {document_id}에 연결할 태그 없음")
            return []

        # 1. 태그 조회 또는 생성 (N+1 문제 방지)
        tags = await self.get_or_create_tags(tag_names)

        # 2. 문서-태그 연결 생성 (N+1 문제 방지)
        tag_ids = [tag.tag_id for tag in tags]
        await self.document_tag_repository.bulk_create(document_id, tag_ids)

        logger.info(f"문서 {document_id}에 태그 {len(tags)}개 연결 완료: {tag_names}")

        return tags

    async def get_tags_by_document_id(self, document_id: int) -> List[Tag]:
        """
        문서 ID로 연결된 모든 태그 조회

        Args:
            document_id: 문서 ID

        Returns:
            Tag 객체 리스트
        """
        return await self.document_tag_repository.find_tags_by_document_id(document_id)

    async def find_tag_by_name(self, name: str) -> Optional[Tag]:
        """
        태그 이름으로 태그 조회

        Args:
            name: 태그 이름

        Returns:
            Tag 객체 또는 None
        """
        return await self.tag_repository.find_by_name(name)
