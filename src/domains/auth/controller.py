# -*- coding: utf-8 -*-
"""Auth 도메인 컨트롤러 (API 엔드포인트)"""
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.session import get_db
from src.domains.users.models import User
from src.domains.auth.service.kakao_service import KakaoOAuthService
from src.domains.auth.service.session_service import SessionService
from src.domains.auth.schema.response import LoginResponse, LogoutResponse, SessionResponse
from src.core.security import get_current_session_data, get_current_user_id
from src.core.config import settings


router = APIRouter()

# 서비스 인스턴스 생성
kakao_service = KakaoOAuthService()
session_service = SessionService()


@router.get("/kakao/login", summary="카카오 로그인 페이지로 리디렉션")
async def kakao_login():
    """
    카카오 인증 서버로 리디렉트하여 사용자 인증을 시작합니다.

    Returns:
        카카오 인증 페이지로의 리디렉션 응답
    """
    kakao_auth_url = (
        f"https://kauth.kakao.com/oauth/authorize?response_type=code"
        f"&client_id={settings.KAKAO_CLIENT_ID}"
        f"&redirect_uri={settings.KAKAO_REDIRECT_URI}"
    )
    return RedirectResponse(kakao_auth_url)


@router.get("/kakao/callback", summary="카카오 인증 콜백 처리")
async def kakao_callback(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    카카오로부터 받은 인가 코드로 사용자를 DB에 저장/조회하고 세션을 생성합니다.

    Args:
        code: 카카오로부터 받은 인가 코드
        db: 데이터베이스 세션

    Returns:
        메인 페이지로의 리디렉션 응답 (세션 ID 쿠키 포함)

    Raises:
        HTTPException: 인증 과정 중 오류 발생 시
    """
    # 1. 카카오 인증 및 사용자 정보 조회
    user_info = await kakao_service.authenticate(code)
    kakao_id = user_info.get("kakao_id")
    nickname = user_info.get("nickname")

    # 2. DB에서 사용자 조회 또는 생성
    result = await db.execute(select(User).where(User.kakao_id == kakao_id))
    user = result.scalar_one_or_none()

    if not user:
        # 신규 사용자 생성
        user = User(
            kakao_id=kakao_id,
            nickname=nickname
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # 3. 세션 생성
    session_id = await session_service.create_session(user.user_id)

    # 4. 쿠키에 세션 ID 설정 후 리디렉션
    # TODO: 프론트엔드 URL로 변경 필요
    response = RedirectResponse(url="/")
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=3600,  # 1시간
        samesite="lax"
    )

    return response


@router.get(
    "/session",
    response_model=SessionResponse,
    summary="현재 사용자 세션 정보 반환"
)
async def get_session(
    request: Request,
    user_id: int = Depends(get_current_user_id)
):
    """
    현재 로그인된 사용자의 세션 정보를 반환합니다.

    Args:
        request: FastAPI Request 객체
        user_id: get_current_user_id 의존성에서 주입된 사용자 ID

    Returns:
        SessionResponse: 사용자 ID와 세션 ID를 포함한 세션 정보
    """
    session_id = request.cookies.get("session_id")
    return SessionResponse(user_id=user_id, session_id=session_id)


@router.get(
    "/me",
    response_model=LoginResponse,
    summary="현재 로그인된 사용자 정보 반환"
)
async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    현재 로그인된 사용자의 상세 정보를 반환합니다.

    Args:
        user_id: get_current_user_id 의존성에서 주입된 사용자 ID
        db: 데이터베이스 세션

    Returns:
        LoginResponse: 사용자 상세 정보

    Raises:
        HTTPException: 사용자를 찾을 수 없는 경우
    """
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )

    return LoginResponse(
        user_id=user.user_id,
        kakao_id=user.kakao_id,
        nickname=user.nickname,
        created_at=user.created_at
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="로그아웃"
)
async def logout(request: Request):
    """
    Redis에서 세션을 삭제하고 쿠키를 만료시킵니다.

    Args:
        request: FastAPI Request 객체

    Returns:
        LogoutResponse: 로그아웃 성공 메시지
    """
    session_id = request.cookies.get("session_id")

    if session_id:
        await session_service.delete_session(session_id)

    response = JSONResponse(
        content={"message": "로그아웃 성공"}
    )
    response.delete_cookie("session_id")

    return response
