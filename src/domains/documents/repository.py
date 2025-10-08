# -*- coding: utf-8 -*-
"""Document 도메인 Repository"""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domains.documents.models import Document


class DocumentRepository:
    """Document 엔티티 데이터 접근 계층"""

    def __init__(self, db: AsyncSession):
        """
        DocumentRepository 초기화

        Args:
            db: SQLAlchemy AsyncSession
        """
        self.db = db

    async def create(
        self,
        user_id: int,
        original_filename: str,
        storage_path: str,
        file_type: str,
        file_size_kb: int
    ) -> Document:
        """
        신규 문서 생성

        Args:
            user_id: 문서 소유자 ID
            original_filename: 원본 파일 이름
            storage_path: MinIO 저장 경로
            file_type: 파일 MIME 타입
            file_size_kb: 파일 크기 (KB)

        Returns:
            생성된 Document 객체
        """
        document = Document(
            user_id=user_id,
            original_filename=original_filename,
            storage_path=storage_path,
            file_type=file_type,
            file_size_kb=file_size_kb
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def find_by_id(self, document_id: int) -> Optional[Document]:
        """
        문서 ID로 문서 조회

        Args:
            document_id: 문서 고유 ID

        Returns:
            Document 객체 또는 None
        """
        result = await self.db.execute(
            select(Document).where(Document.document_id == document_id)
        )
        return result.scalar_one_or_none()

    async def find_by_id_and_user_id(
        self,
        document_id: int,
        user_id: int
    ) -> Optional[Document]:
        """
        문서 ID와 사용자 ID로 문서 조회 (권한 검증용)

        Args:
            document_id: 문서 고유 ID
            user_id: 사용자 ID

        Returns:
            Document 객체 또는 None
        """
        result = await self.db.execute(
            select(Document).where(
                Document.document_id == document_id,
                Document.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def find_all_by_user_id(self, user_id: int) -> List[Document]:
        """
        사용자 ID로 모든 문서 조회

        Args:
            user_id: 사용자 ID

        Returns:
            Document 객체 리스트
        """
        result = await self.db.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.uploaded_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, document: Document) -> bool:
        """
        문서 삭제

        Args:
            document: 삭제할 Document 객체

        Returns:
            삭제 성공 여부
        """
        try:
            await self.db.delete(document)
            await self.db.commit()
            return True
        except Exception:
            await self.db.rollback()
            return False
