# -*- coding: utf-8 -*-
"""Document 도메인 스키마"""
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """문서 업로드 응답 스키마"""
    document_id: int = Field(..., description="문서 고유 ID")
    user_id: int = Field(..., description="문서 소유자 ID")
    original_filename: str = Field(..., description="원본 파일 이름")
    storage_path: str = Field(..., description="MinIO 저장 경로")
    file_type: str = Field(..., description="파일 MIME 타입")
    file_size_kb: int = Field(..., description="파일 크기 (KB)")
    uploaded_at: datetime = Field(..., description="업로드 일시")
    updated_at: datetime = Field(..., description="최종 수정 일시")

    class Config:
        from_attributes = True  # ORM 모델 → Pydantic 변환 지원


class DocumentListResponse(BaseModel):
    """문서 목록 조회 응답 스키마"""
    document_id: int = Field(..., description="문서 고유 ID")
    original_filename: str = Field(..., description="원본 파일 이름")
    file_type: str = Field(..., description="파일 MIME 타입")
    file_size_kb: int = Field(..., description="파일 크기 (KB)")
    uploaded_at: datetime = Field(..., description="업로드 일시")
    updated_at: datetime = Field(..., description="최종 수정 일시")

    class Config:
        from_attributes = True


class DocumentDetailResponse(BaseModel):
    """문서 상세 조회 응답 스키마"""
    document_id: int = Field(..., description="문서 고유 ID")
    user_id: int = Field(..., description="문서 소유자 ID")
    original_filename: str = Field(..., description="원본 파일 이름")
    storage_path: str = Field(..., description="MinIO 저장 경로")
    file_type: str = Field(..., description="파일 MIME 타입")
    file_size_kb: int = Field(..., description="파일 크기 (KB)")
    uploaded_at: datetime = Field(..., description="업로드 일시")
    updated_at: datetime = Field(..., description="최종 수정 일시")

    class Config:
        from_attributes = True


class DocumentDeleteResponse(BaseModel):
    """문서 삭제 응답 스키마"""
    message: str = Field(..., description="삭제 결과 메시지")
    document_id: int = Field(..., description="삭제된 문서 ID")
