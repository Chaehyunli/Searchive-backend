# -*- coding: utf-8 -*-
"""User 도메인 스키마"""
from datetime import datetime
from pydantic import BaseModel, Field


class UserCreateRequest(BaseModel):
    """사용자 생성 요청 스키마"""
    kakao_id: str = Field(..., description="카카오 소셜 ID")
    nickname: str = Field(..., description="사용자 닉네임")


class UserUpdateRequest(BaseModel):
    """사용자 정보 수정 요청 스키마"""
    nickname: str = Field(..., description="새로운 닉네임")


class UserResponse(BaseModel):
    """사용자 정보 응답 스키마"""
    user_id: int = Field(..., description="사용자 고유 ID")
    kakao_id: str = Field(..., description="카카오 소셜 ID")
    nickname: str = Field(..., description="사용자 닉네임")
    created_at: datetime = Field(..., description="가입 일시")

    class Config:
        from_attributes = True  # ORM 모델 → Pydantic 변환 지원


class UserDeleteResponse(BaseModel):
    """사용자 삭제 응답 스키마"""
    message: str = Field(..., description="삭제 결과 메시지")
    user_id: int = Field(..., description="삭제된 사용자 ID")
