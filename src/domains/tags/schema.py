# -*- coding: utf-8 -*-
"""Tag 도메인 스키마"""
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class TagResponse(BaseModel):
    """태그 응답 스키마"""
    tag_id: int = Field(..., description="태그 고유 ID")
    name: str = Field(..., description="태그 이름")
    created_at: datetime = Field(..., description="생성 일시")

    class Config:
        from_attributes = True


class DocumentTagResponse(BaseModel):
    """문서에 연결된 태그 응답 스키마"""
    document_id: int = Field(..., description="문서 ID")
    tags: List[TagResponse] = Field(..., description="태그 리스트")

    class Config:
        from_attributes = True


class TagCreateRequest(BaseModel):
    """태그 생성 요청 스키마"""
    name: str = Field(..., min_length=1, max_length=100, description="태그 이름")


class ExtractedKeywordsResponse(BaseModel):
    """추출된 키워드 응답 스키마"""
    keywords: List[str] = Field(..., description="추출된 키워드 리스트")
    extraction_method: str = Field(..., description="추출 방법 (keybert 또는 elasticsearch)")
    document_count: int = Field(..., description="전체 문서 수")
