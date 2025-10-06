# -*- coding: utf-8 -*-
"""Auth 도메인 Response DTO"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class KakaoTokenResponse(BaseModel):
    """카카오 토큰 응답 DTO"""
    access_token: str = Field(..., description="액세스 토큰")
    token_type: str = Field(..., description="토큰 타입 (Bearer)")
    refresh_token: Optional[str] = Field(None, description="리프레시 토큰")
    expires_in: int = Field(..., description="액세스 토큰 만료 시간(초)")
    scope: Optional[str] = Field(None, description="권한 범위")


class KakaoUserInfo(BaseModel):
    """카카오 사용자 정보 DTO"""
    id: int = Field(..., description="카카오 사용자 ID")
    kakao_account: Optional[dict] = Field(None, description="카카오 계정 정보")
    properties: Optional[dict] = Field(None, description="사용자 속성 (닉네임 등)")


class SessionResponse(BaseModel):
    """세션 정보 응답 DTO"""
    user_id: int = Field(..., description="사용자 ID")
    session_id: Optional[str] = Field(None, description="세션 ID")


class LoginResponse(BaseModel):
    """로그인 응답 DTO"""
    user_id: int = Field(..., description="사용자 ID")
    kakao_id: str = Field(..., description="카카오 ID")
    nickname: Optional[str] = Field(None, description="닉네임")
    created_at: datetime = Field(..., description="가입일시")
    message: str = Field(default="로그인 성공", description="응답 메시지")


class LogoutResponse(BaseModel):
    """로그아웃 응답 DTO"""
    message: str = Field(default="로그아웃 성공", description="응답 메시지")
