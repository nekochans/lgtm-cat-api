# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from domain.lgtm_image_errors import (
    ErrExpiredToken,
    ErrInvalidToken,
    ErrJwksFetchFailed,
)
from domain.repository.jwt_token_verifier_repository_interface import (
    JwtTokenVerifierRepositoryInterface,
)
from presentation.dependencies.auth import verify_token


class TestVerifyToken:
    @pytest.mark.asyncio
    async def test_verify_token_success_with_valid_bearer_token(self) -> None:
        """正常系: 有効なBearerトークンで検証に成功し、Bearerプレフィックスを正しく除去する."""
        # Arrange
        mock_verifier = AsyncMock(spec=JwtTokenVerifierRepositoryInterface)
        expected_payload: dict[str, Any] = {
            "sub": "user123",
            "email": "test@example.com",
            "exp": 1234567890,
        }
        mock_verifier.verify.return_value = expected_payload

        token_value = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIn0"
        authorization = f"Bearer {token_value}"

        # Act
        result = await verify_token(mock_verifier, authorization)

        # Assert
        assert result == expected_payload
        # "Bearer "を除去した正しいトークンが渡されることを確認
        mock_verifier.verify.assert_called_once_with(token_value)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "authorization_header",
        [
            "Bearer valid_token_123",
            "bearer valid_token_123",
            "BEARER valid_token_123",
            "BeArEr valid_token_123",
        ],
    )
    async def test_verify_token_accepts_case_insensitive_bearer_scheme(
        self, authorization_header: str
    ) -> None:
        """正常系: 大文字小文字が混在するBearerスキームでも検証に成功する."""
        # Arrange
        mock_verifier = AsyncMock(spec=JwtTokenVerifierRepositoryInterface)
        expected_payload: dict[str, Any] = {"sub": "user123"}
        mock_verifier.verify.return_value = expected_payload
        token_value = "valid_token_123"

        # Act
        result = await verify_token(mock_verifier, authorization_header)

        # Assert
        assert result == expected_payload
        mock_verifier.verify.assert_called_once_with(token_value)

    @pytest.mark.asyncio
    async def test_verify_token_handles_whitespace_around_token(self) -> None:
        """正常系: トークンの前後に空白がある場合は削除して検証する."""
        # Arrange
        mock_verifier = AsyncMock(spec=JwtTokenVerifierRepositoryInterface)
        expected_payload: dict[str, Any] = {"sub": "user123"}
        mock_verifier.verify.return_value = expected_payload

        token_value = "valid_token_123"
        authorization = f"Bearer   {token_value}   "  # 前後に空白

        # Act
        result = await verify_token(mock_verifier, authorization)

        # Assert
        assert result == expected_payload
        # 空白が削除されたトークンが渡されることを確認
        mock_verifier.verify.assert_called_once_with(token_value)

    @pytest.mark.asyncio
    async def test_verify_token_raises_401_when_authorization_header_missing_bearer(
        self,
    ) -> None:
        """異常系: Bearerプレフィックスがない場合は401エラーを返す."""
        # Arrange
        mock_verifier = AsyncMock(spec=JwtTokenVerifierRepositoryInterface)
        authorization = "InvalidToken"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(mock_verifier, authorization)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid authorization header"
        mock_verifier.verify.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_token_raises_401_when_authorization_header_is_empty(
        self,
    ) -> None:
        """異常系: Authorizationヘッダーが空の場合は401エラーを返す."""
        # Arrange
        mock_verifier = AsyncMock(spec=JwtTokenVerifierRepositoryInterface)
        authorization = ""

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(mock_verifier, authorization)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid authorization header"
        mock_verifier.verify.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_token_raises_401_when_token_is_only_whitespace(
        self,
    ) -> None:
        """異常系: トークン部分が空白のみの場合は401エラーを返す."""
        # Arrange
        mock_verifier = AsyncMock(spec=JwtTokenVerifierRepositoryInterface)
        authorization = "Bearer    "  # 空白のみ

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(mock_verifier, authorization)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid authorization header"
        mock_verifier.verify.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_token_raises_401_when_bearer_without_token(self) -> None:
        """異常系: "Bearer"のみでトークンがない場合は401エラーを返す."""
        # Arrange
        mock_verifier = AsyncMock(spec=JwtTokenVerifierRepositoryInterface)
        authorization = "Bearer"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(mock_verifier, authorization)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid authorization header"
        mock_verifier.verify.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_token_raises_401_when_token_is_invalid(self) -> None:
        """異常系: トークンが無効な場合は401エラーを返す."""
        # Arrange
        mock_verifier = AsyncMock(spec=JwtTokenVerifierRepositoryInterface)
        mock_verifier.verify.side_effect = ErrInvalidToken("Invalid token format")

        authorization = "Bearer malformed_token"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(mock_verifier, authorization)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token format"
        mock_verifier.verify.assert_called_once_with("malformed_token")

    @pytest.mark.asyncio
    async def test_verify_token_raises_401_when_token_is_expired(self) -> None:
        """異常系: トークンが期限切れの場合は401エラーを返す."""
        # Arrange
        mock_verifier = AsyncMock(spec=JwtTokenVerifierRepositoryInterface)
        mock_verifier.verify.side_effect = ErrExpiredToken("Token has expired")

        authorization = "Bearer expired_token"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(mock_verifier, authorization)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token has expired"
        mock_verifier.verify.assert_called_once_with("expired_token")

    @pytest.mark.asyncio
    async def test_verify_token_raises_401_when_unexpected_exception_occurs(
        self,
    ) -> None:
        """異常系: 予期しない例外が発生した場合は401エラーを返す."""
        # Arrange
        mock_verifier = AsyncMock(spec=JwtTokenVerifierRepositoryInterface)
        mock_verifier.verify.side_effect = RuntimeError("Unexpected error")

        authorization = "Bearer some_token"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(mock_verifier, authorization)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token verification failed"
        mock_verifier.verify.assert_called_once_with("some_token")

    @pytest.mark.asyncio
    async def test_verify_token_raises_503_when_jwks_fetch_fails(self) -> None:
        """異常系: JWKS取得に失敗した場合は503エラーを返す."""
        # Arrange
        mock_verifier = AsyncMock(spec=JwtTokenVerifierRepositoryInterface)
        mock_verifier.verify.side_effect = ErrJwksFetchFailed("Failed to fetch JWKS")

        authorization = "Bearer valid_token"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(mock_verifier, authorization)

        assert exc_info.value.status_code == 503
        assert exc_info.value.detail == "Failed to fetch JWKS"
        mock_verifier.verify.assert_called_once_with("valid_token")
