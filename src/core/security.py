# -*- coding: utf-8 -*-
"""보안 관련 의존성 및 유틸리티 함수"""
import json
from typing import Dict
from fastapi import Request, Depends, HTTPException, status
from src.core.redis import redis_client


async def get_current_session_data(request: Request) -> Dict:
    """
    쿠키의 세션 ID를 검증하고 Redis에 저장된 세션 데이터를 반환합니다.

    Args:
        request: FastAPI Request 객체

    Returns:
        세션 데이터 딕셔너리 (예: {"user_id": 123})

    Raises:
        HTTPException: 세션이 없거나 유효하지 않은 경우 401 에러

    Usage:
        @router.get("/protected")
        async def protected_route(session: dict = Depends(get_current_session_data)):
            user_id = session.get("user_id")
            ...
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    session_data_json = await redis_client.get(f"session:{session_id}")
    if not session_data_json:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )

    return json.loads(session_data_json)


async def get_current_user_id(
    session_data: Dict = Depends(get_current_session_data)
) -> int:
    """
    현재 로그인한 사용자의 ID를 반환합니다.

    Args:
        session_data: get_current_session_data에서 반환된 세션 데이터

    Returns:
        사용자 ID (user_id)

    Usage:
        @router.get("/me")
        async def get_me(user_id: int = Depends(get_current_user_id)):
            ...
    """
    return session_data.get("user_id")
