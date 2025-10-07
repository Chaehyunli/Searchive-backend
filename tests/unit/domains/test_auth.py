# -*- coding: utf-8 -*-
"""Auth 도메인 테스트"""
import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, status
from httpx import AsyncClient

from src.domains.auth.service.kakao_service import KakaoOAuthService
from src.domains.auth.service.session_service import SessionService


# ============================================
# KakaoOAuthService Tests
# ============================================

class TestKakaoOAuthService:
    """KakaoOAuthService 테스트"""

    @pytest.fixture
    def kakao_service(self):
        """KakaoOAuthService 인스턴스"""
        return KakaoOAuthService()

    @pytest.mark.asyncio
    async def test_get_access_token_success(self, kakao_service):
        """액세스 토큰 발급 성공 테스트"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "bearer",
            "expires_in": 3600
        }

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            access_token = await kakao_service.get_access_token("test_code")
            assert access_token == "test_access_token"

    @pytest.mark.asyncio
    async def test_get_access_token_no_token_in_response(self, kakao_service):
        """액세스 토큰이 응답에 없는 경우 테스트"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            with pytest.raises(HTTPException) as exc_info:
                await kakao_service.get_access_token("test_code")

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "액세스 토큰이 응답에 포함되지 않았습니다" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_access_token_rate_limit(self, kakao_service):
        """카카오 API Rate Limit 에러 테스트"""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "error_code": "KOE237",
            "error_description": "API rate limit exceeded"
        }

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            with pytest.raises(HTTPException) as exc_info:
                await kakao_service.get_access_token("test_code")

            assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            assert "너무 많습니다" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_access_token_invalid_code(self, kakao_service):
        """유효하지 않은 인가 코드 테스트"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error_code": "KOE320",
            "error_description": "Invalid authorization code"
        }

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            with pytest.raises(HTTPException) as exc_info:
                await kakao_service.get_access_token("invalid_code")

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "만료되었습니다" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_user_info_success(self, kakao_service):
        """사용자 정보 조회 성공 테스트"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 12345,
            "properties": {
                "nickname": "테스트유저"
            },
            "kakao_account": {
                "email": "test@example.com"
            }
        }

        with patch("httpx.AsyncClient.get", return_value=mock_response):
            user_info = await kakao_service.get_user_info("test_access_token")

            assert user_info["kakao_id"] == "12345"
            assert user_info["nickname"] == "테스트유저"
            assert user_info["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_info_no_kakao_id(self, kakao_service):
        """카카오 ID가 없는 경우 테스트"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": None,  # ID가 None인 경우
            "properties": {},
            "kakao_account": {}
        }

        with patch("httpx.AsyncClient.get", return_value=mock_response):
            user_info = await kakao_service.get_user_info("test_access_token")
            # ID가 None이면 str(None)으로 변환되어 "None"이 반환됨
            assert user_info["kakao_id"] == "None"

    @pytest.mark.asyncio
    async def test_get_user_info_api_failure(self, kakao_service):
        """사용자 정보 조회 API 실패 테스트"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("httpx.AsyncClient.get", return_value=mock_response):
            with pytest.raises(HTTPException) as exc_info:
                await kakao_service.get_user_info("invalid_token")

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "사용자 정보 조회 실패" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_authenticate_success(self, kakao_service):
        """카카오 인증 전체 플로우 성공 테스트"""
        # Mock access token response
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            "access_token": "test_access_token"
        }

        # Mock user info response
        mock_user_info_response = MagicMock()
        mock_user_info_response.status_code = 200
        mock_user_info_response.json.return_value = {
            "id": 12345,
            "properties": {"nickname": "테스트유저"},
            "kakao_account": {"email": "test@example.com"}
        }

        with patch("httpx.AsyncClient.post", return_value=mock_token_response), \
             patch("httpx.AsyncClient.get", return_value=mock_user_info_response):
            user_info = await kakao_service.authenticate("test_code")

            assert user_info["kakao_id"] == "12345"
            assert user_info["nickname"] == "테스트유저"
            assert user_info["email"] == "test@example.com"


# ============================================
# SessionService Tests
# ============================================

class TestSessionService:
    """SessionService 테스트"""

    @pytest.mark.asyncio
    async def test_create_session_success(self):
        """세션 생성 성공 테스트"""
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()

        with patch("src.domains.auth.service.session_service.redis_client", mock_redis):
            session_service = SessionService()
            session_id = await session_service.create_session(user_id=123)

            # UUID 형식 확인
            assert uuid.UUID(session_id)

            # Redis setex 호출 확인
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args
            assert call_args[0][0].startswith("session:")
            assert call_args[0][1] == 3600  # expire time
            assert '"user_id": 123' in call_args[0][2]

    @pytest.mark.asyncio
    async def test_get_session_success(self):
        """세션 조회 성공 테스트"""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value='{"user_id": 123}')

        with patch("src.domains.auth.service.session_service.redis_client", mock_redis):
            session_service = SessionService()
            session_data = await session_service.get_session("test_session_id")

            assert session_data is not None
            assert session_data["user_id"] == 123
            mock_redis.get.assert_called_once_with("session:test_session_id")

    @pytest.mark.asyncio
    async def test_get_session_not_found(self):
        """세션이 존재하지 않는 경우 테스트"""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        with patch("src.domains.auth.service.session_service.redis_client", mock_redis):
            session_service = SessionService()
            session_data = await session_service.get_session("invalid_session_id")

            assert session_data is None
            mock_redis.get.assert_called_once_with("session:invalid_session_id")

    @pytest.mark.asyncio
    async def test_delete_session_success(self):
        """세션 삭제 성공 테스트"""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)

        with patch("src.domains.auth.service.session_service.redis_client", mock_redis):
            session_service = SessionService()
            result = await session_service.delete_session("test_session_id")

            assert result is True
            mock_redis.delete.assert_called_once_with("session:test_session_id")

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self):
        """존재하지 않는 세션 삭제 테스트"""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=0)

        with patch("src.domains.auth.service.session_service.redis_client", mock_redis):
            session_service = SessionService()
            result = await session_service.delete_session("invalid_session_id")

            assert result is False
            mock_redis.delete.assert_called_once_with("session:invalid_session_id")

    @pytest.mark.asyncio
    async def test_extend_session_success(self):
        """세션 만료 시간 연장 성공 테스트"""
        mock_redis = AsyncMock()
        mock_redis.expire = AsyncMock(return_value=1)

        with patch("src.domains.auth.service.session_service.redis_client", mock_redis):
            session_service = SessionService()
            result = await session_service.extend_session("test_session_id")

            assert result is True
            mock_redis.expire.assert_called_once_with("session:test_session_id", 3600)

    @pytest.mark.asyncio
    async def test_extend_session_not_found(self):
        """존재하지 않는 세션 연장 테스트"""
        mock_redis = AsyncMock()
        mock_redis.expire = AsyncMock(return_value=0)

        with patch("src.domains.auth.service.session_service.redis_client", mock_redis):
            session_service = SessionService()
            result = await session_service.extend_session("invalid_session_id")

            assert result is False
            mock_redis.expire.assert_called_once_with("session:invalid_session_id", 3600)
