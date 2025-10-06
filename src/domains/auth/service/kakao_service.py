# -*- coding: utf-8 -*-
"""카카오 OAuth API 통신 서비스"""
import httpx
from typing import Dict, Optional
from fastapi import HTTPException, status
from src.core.config import settings


class KakaoOAuthService:
    """카카오 OAuth 관련 비즈니스 로직을 담당하는 서비스 클래스"""

    TOKEN_URL = "https://kauth.kakao.com/oauth/token"
    USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"

    def __init__(self):
        """KakaoOAuthService 초기화"""
        self.client_id = settings.KAKAO_CLIENT_ID
        self.client_secret = settings.KAKAO_CLIENT_SECRET
        self.redirect_uri = settings.KAKAO_REDIRECT_URI

    async def get_access_token(self, code: str) -> str:
        """
        카카오로부터 인가 코드를 사용하여 액세스 토큰을 발급받습니다.

        Args:
            code: 카카오로부터 받은 인가 코드

        Returns:
            액세스 토큰 문자열

        Raises:
            HTTPException: 토큰 발급 실패 시
        """
        token_data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }

        # client_secret이 있는 경우에만 추가 (선택적)
        if self.client_secret:
            token_data["client_secret"] = self.client_secret

        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL, data=token_data)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"액세스 토큰 발급 실패: {response.text}"
                )

            token_response = response.json()
            access_token = token_response.get("access_token")

            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="액세스 토큰이 응답에 포함되지 않았습니다"
                )

            return access_token

    async def get_user_info(self, access_token: str) -> Dict:
        """
        액세스 토큰을 사용하여 카카오 사용자 정보를 조회합니다.

        Args:
            access_token: 카카오 액세스 토큰

        Returns:
            사용자 정보 딕셔너리 (kakao_id, nickname, email 포함)

        Raises:
            HTTPException: 사용자 정보 조회 실패 시
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(self.USER_INFO_URL, headers=headers)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"사용자 정보 조회 실패: {response.text}"
                )

            user_info_response = response.json()

            # 필수 정보 추출
            kakao_id = str(user_info_response.get("id"))
            properties = user_info_response.get("properties", {})
            kakao_account = user_info_response.get("kakao_account", {})

            nickname = properties.get("nickname")
            email = kakao_account.get("email")

            if not kakao_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="카카오 사용자 ID를 찾을 수 없습니다"
                )

            return {
                "kakao_id": kakao_id,
                "nickname": nickname,
                "email": email
            }

    async def authenticate(self, code: str) -> Dict:
        """
        인가 코드로 카카오 인증을 완료하고 사용자 정보를 반환합니다.

        Args:
            code: 카카오로부터 받은 인가 코드

        Returns:
            사용자 정보 딕셔너리 (kakao_id, nickname, email)

        Raises:
            HTTPException: 인증 과정 중 오류 발생 시
        """
        # 1. 액세스 토큰 발급
        access_token = await self.get_access_token(code)

        # 2. 사용자 정보 조회
        user_info = await self.get_user_info(access_token)

        return user_info
