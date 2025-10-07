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


@router.post("/test/login", summary="[개발 전용] 테스트 로그인")
async def test_login(
    kakao_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    개발 환경에서만 사용 가능한 테스트 로그인 엔드포인트.
    카카오 OAuth 없이 직접 로그인할 수 있습니다.

    Args:
        kakao_id: 로그인할 카카오 ID (예: "test_user_123")
        db: 데이터베이스 세션

    Returns:
        세션 ID 쿠키가 포함된 로그인 성공 응답

    Raises:
        HTTPException: 개발 환경이 아닌 경우 403 에러
    """
    # 운영 환경에서는 사용 불가
    if settings.APP_ENV != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="테스트 로그인은 개발 환경에서만 사용 가능합니다"
        )

    # 사용자 조회 또는 생성
    result = await db.execute(select(User).where(User.kakao_id == kakao_id))
    user = result.scalar_one_or_none()

    if not user:
        # 신규 사용자 생성
        user = User(
            kakao_id=kakao_id,
            nickname=f"테스트유저_{kakao_id}"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # 세션 생성
    session_id = await session_service.create_session(user.user_id)

    # 응답에 쿠키 설정
    response = JSONResponse(
        content={
            "message": "테스트 로그인 성공",
            "user_id": user.user_id,
            "kakao_id": user.kakao_id,
            "nickname": user.nickname
        }
    )
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=3600,
        samesite="lax"
    )

    return response


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
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"카카오 콜백 시작 - code: {code[:10]}...")

        # 0. 코드 중복 사용 방지 - 이미 사용된 코드인지 확인
        existing_session = await session_service.get_session_by_code(code)
        if existing_session:
            logger.info(f"이미 사용된 코드 - 기존 세션 사용: {existing_session[:10]}...")
            # 이미 사용된 코드라면 기존 세션으로 리디렉션
            frontend_callback_url = f"{settings.FRONTEND_URL}/auth/kakao/callback"
            response = RedirectResponse(url=frontend_callback_url)
            response.set_cookie(
                key="session_id",
                value=existing_session,
                httponly=True,
                max_age=3600,
                samesite="lax"
            )
            return response

        # 0-1. 코드 처리 중 플래그 설정 (동시 요청 방지)
        code_lock_key = f"kakao_code_lock:{code}"
        from src.core.redis import redis_client
        is_processing = await redis_client.get(code_lock_key)

        if is_processing:
            logger.warning(f"이미 처리 중인 코드 - 대기 중...")
            # 이미 처리 중이면 1초 대기 후 세션 확인
            import asyncio
            await asyncio.sleep(1)
            existing_session = await session_service.get_session_by_code(code)
            if existing_session:
                logger.info(f"처리 완료된 세션 사용: {existing_session[:10]}...")
                frontend_callback_url = f"{settings.FRONTEND_URL}/auth/kakao/callback"
                response = RedirectResponse(url=frontend_callback_url)
                response.set_cookie(
                    key="session_id",
                    value=existing_session,
                    httponly=True,
                    max_age=3600,
                    samesite="lax"
                )
                return response
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="로그인 처리 중입니다. 잠시 후 다시 시도해주세요."
                )

        # 코드 처리 시작 플래그 설정 (30초 유효)
        await redis_client.setex(code_lock_key, 30, "processing")

        # 1. 카카오 인증 및 사용자 정보 조회
        logger.info("카카오 API 호출 시작")
        user_info = await kakao_service.authenticate(code)
        kakao_id = user_info.get("kakao_id")
        nickname = user_info.get("nickname")
        logger.info(f"카카오 인증 성공 - kakao_id: {kakao_id}, nickname: {nickname}")

        # 2. DB에서 사용자 조회 또는 생성
        result = await db.execute(select(User).where(User.kakao_id == kakao_id))
        user = result.scalar_one_or_none()

        if not user:
            logger.info("신규 사용자 생성")
            # 신규 사용자 생성
            user = User(
                kakao_id=kakao_id,
                nickname=nickname
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            logger.info(f"기존 사용자 조회 - user_id: {user.user_id}")

        # 3. 세션 생성
        session_id = await session_service.create_session(user.user_id)
        logger.info(f"세션 생성 완료 - session_id: {session_id[:10]}...")

        # 4. 코드와 세션 ID 매핑 저장 (10분 동안 유효)
        await session_service.save_code_session_mapping(code, session_id)

        # 5. 쿠키에 세션 ID 설정 후 프론트엔드 콜백 페이지로 리디렉션
        frontend_callback_url = f"{settings.FRONTEND_URL}/auth/kakao/callback"
        response = RedirectResponse(url=frontend_callback_url)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=3600,  # 1시간
            samesite="lax"
        )

        logger.info(f"콜백 처리 완료 - 리디렉션: {frontend_callback_url}")
        return response

    except Exception as e:
        logger.error(f"카카오 콜백 처리 중 에러 발생: {str(e)}", exc_info=True)
        raise


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
    import logging
    logger = logging.getLogger(__name__)

    session_id = request.cookies.get("session_id")
    logger.info(f"로그아웃 요청 - session_id: {session_id}")

    if session_id:
        deleted = await session_service.delete_session(session_id)
        logger.info(f"세션 삭제 결과: {deleted} (session_id: {session_id[:10] if session_id else 'None'}...)")
    else:
        logger.warning("세션 ID가 없는 로그아웃 요청")

    response = JSONResponse(
        content={"message": "로그아웃 성공"}
    )
    response.delete_cookie("session_id")

    logger.info("로그아웃 완료")
    return response
