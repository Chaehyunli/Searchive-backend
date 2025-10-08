# -*- coding: utf-8 -*-
"""Document 도메인 Service"""
from typing import List, Optional
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from src.domains.documents.repository import DocumentRepository
from src.domains.documents.models import Document
from src.core.minio_client import minio_client
import logging

logger = logging.getLogger(__name__)

# 허용된 파일 형식 (MIME 타입)
ALLOWED_MIME_TYPES = {
    "application/pdf",  # .pdf
    "text/plain",  # .txt
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.ms-excel",  # .xls
    "application/msword",  # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.ms-powerpoint",  # .ppt
    "application/vnd.openxmlformats-officedocument.presentationml.presentation"  # .pptx
}


class DocumentService:
    """Document 비즈니스 로직 처리 계층"""

    def __init__(self, document_repository: DocumentRepository):
        """
        DocumentService 초기화

        Args:
            document_repository: DocumentRepository 인스턴스
        """
        self.document_repository = document_repository

    async def upload_document(
        self,
        user_id: int,
        file: UploadFile
    ) -> Document:
        """
        문서 업로드 (파일 검증 → MinIO 저장 → DB 저장)

        Args:
            user_id: 업로드하는 사용자 ID
            file: 업로드된 파일

        Returns:
            생성된 Document 객체

        Raises:
            HTTPException: 파일 형식이 허용되지 않거나 업로드 실패 시
        """
        # 1. 파일 형식 검증
        if file.content_type not in ALLOWED_MIME_TYPES:
            logger.warning(f"허용되지 않은 파일 형식: {file.content_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원하지 않는 파일 형식입니다: {file.content_type}. 텍스트 기반 문서만 업로드 가능합니다."
            )

        # 2. 고유 경로 생성 (user_id/uuid.확장자)
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        storage_path = f"{user_id}/{unique_filename}"

        # 3. 파일 크기 계산 (KB)
        file_data = await file.read()
        file_size_bytes = len(file_data)
        file_size_kb = file_size_bytes // 1024

        try:
            # 4. MinIO에 파일 업로드
            from io import BytesIO
            file_stream = BytesIO(file_data)

            minio_client.upload_file(
                file_path=storage_path,
                file_data=file_stream,
                file_size=file_size_bytes,
                content_type=file.content_type
            )
            logger.info(f"MinIO 업로드 성공: {storage_path}")

            # 5. PostgreSQL에 메타데이터 저장
            document = await self.document_repository.create(
                user_id=user_id,
                original_filename=file.filename,
                storage_path=storage_path,
                file_type=file.content_type,
                file_size_kb=file_size_kb
            )
            logger.info(f"문서 메타데이터 저장 성공: document_id={document.document_id}")

            return document

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"문서 업로드 실패: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="문서 업로드 중 오류가 발생했습니다."
            )

    async def get_user_documents(self, user_id: int) -> List[Document]:
        """
        사용자의 모든 문서 조회

        Args:
            user_id: 사용자 ID

        Returns:
            Document 객체 리스트
        """
        return await self.document_repository.find_all_by_user_id(user_id)

    async def get_document_by_id(
        self,
        document_id: int,
        user_id: int
    ) -> Optional[Document]:
        """
        특정 문서 조회 (권한 검증 포함)

        Args:
            document_id: 문서 ID
            user_id: 요청하는 사용자 ID

        Returns:
            Document 객체 또는 None
        """
        return await self.document_repository.find_by_id_and_user_id(
            document_id=document_id,
            user_id=user_id
        )

    async def delete_document(
        self,
        document_id: int,
        user_id: int
    ) -> bool:
        """
        문서 삭제 (MinIO 파일 삭제 + DB 삭제)

        Args:
            document_id: 삭제할 문서 ID
            user_id: 요청하는 사용자 ID

        Returns:
            삭제 성공 여부

        Raises:
            HTTPException: 문서를 찾을 수 없거나 삭제 실패 시
        """
        # 1. 문서 조회 (권한 검증)
        document = await self.document_repository.find_by_id_and_user_id(
            document_id=document_id,
            user_id=user_id
        )

        if not document:
            logger.warning(f"문서 찾을 수 없음: document_id={document_id}, user_id={user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="문서를 찾을 수 없습니다."
            )

        try:
            # 2. MinIO에서 파일 삭제
            minio_client.delete_file(document.storage_path)
            logger.info(f"MinIO 파일 삭제 성공: {document.storage_path}")

            # 3. PostgreSQL에서 메타데이터 삭제 (CASCADE로 관련 태그도 자동 삭제)
            success = await self.document_repository.delete(document)

            if success:
                logger.info(f"문서 삭제 성공: document_id={document_id}")
                return True
            else:
                logger.error(f"DB에서 문서 삭제 실패: document_id={document_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="문서 삭제 중 오류가 발생했습니다."
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"문서 삭제 실패: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="문서 삭제 중 오류가 발생했습니다."
            )
