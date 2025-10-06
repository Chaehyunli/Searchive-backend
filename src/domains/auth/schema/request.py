# -*- coding: utf-8 -*-
"""Auth 도메인 Request DTO"""
from pydantic import BaseModel, Field
from typing import Optional


class KakaoCallbackRequest(BaseModel):
    """카카오 인증 콜백 요청 DTO"""
    code: str = Field(..., description="카카오로부터 받은 인가 코드")
    state: Optional[str] = Field(None, description="CSRF 방지를 위한 state 파라미터")


class SessionCreateRequest(BaseModel):
    """세션 생성 요청 DTO"""
    user_id: int = Field(..., description="사용자 ID")


class LogoutRequest(BaseModel):
    """로그아웃 요청 DTO (필요 시 사용)"""
    pass
