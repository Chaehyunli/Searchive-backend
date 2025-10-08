# -*- coding: utf-8 -*-
"""MinIO 클라이언트 유틸리티"""
from minio import Minio
from minio.error import S3Error
from src.core.config import settings
import logging

logger = logging.getLogger(__name__)


class MinIOClient:
    """MinIO 클라이언트 래퍼 클래스"""

    def __init__(self):
        """MinIO 클라이언트 초기화"""
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME

    async def ensure_bucket_exists(self):
        """버킷이 없으면 생성"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"MinIO 버킷 생성: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"MinIO 버킷 확인/생성 중 오류: {e}")
            raise

    def upload_file(self, file_path: str, file_data, file_size: int, content_type: str):
        """
        MinIO에 파일 업로드

        Args:
            file_path: MinIO에 저장할 파일 경로 (예: 1/uuid.pdf)
            file_data: 파일 데이터 (바이트 스트림)
            file_size: 파일 크기 (바이트)
            content_type: 파일 MIME 타입

        Returns:
            업로드된 파일의 저장 경로

        Raises:
            S3Error: MinIO 업로드 실패 시
        """
        try:
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=file_path,
                data=file_data,
                length=file_size,
                content_type=content_type
            )
            logger.info(f"MinIO 업로드 성공: {file_path}")
            return file_path
        except S3Error as e:
            logger.error(f"MinIO 업로드 실패: {e}")
            raise

    def delete_file(self, file_path: str):
        """
        MinIO에서 파일 삭제

        Args:
            file_path: 삭제할 파일 경로

        Raises:
            S3Error: MinIO 삭제 실패 시
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=file_path
            )
            logger.info(f"MinIO 삭제 성공: {file_path}")
        except S3Error as e:
            logger.error(f"MinIO 삭제 실패: {e}")
            raise

    def get_file_url(self, file_path: str, expires: int = 3600) -> str:
        """
        MinIO에서 파일의 임시 접근 URL 생성

        Args:
            file_path: 파일 경로
            expires: URL 만료 시간 (초, 기본 1시간)

        Returns:
            파일 다운로드 URL
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=file_path,
                expires=expires
            )
            return url
        except S3Error as e:
            logger.error(f"MinIO URL 생성 실패: {e}")
            raise


# 전역 MinIO 클라이언트 인스턴스
minio_client = MinIOClient()
