# 絶対厳守：編集前に必ずAI実装ルールを読む

import time
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from domain.lgtm_image_errors import ErrInvalidToken, ErrJwksFetchFailed
from infrastructure.cognito_token_verifier_repository import (
    JWKS_CACHE_TTL,
    CognitoTokenVerifierRepository,
)


class TestCognitoTokenVerifierRepository:
    @pytest.fixture
    def mock_jwks(self) -> dict[str, Any]:
        """モックJWKSデータを返すフィクスチャ."""
        return {
            "keys": [
                {
                    "kid": "test-key-id-1",
                    "kty": "RSA",
                    "use": "sig",
                    "n": "test-n-value",
                    "e": "AQAB",
                },
                {
                    "kid": "test-key-id-2",
                    "kty": "RSA",
                    "use": "sig",
                    "n": "test-n-value-2",
                    "e": "AQAB",
                },
            ]
        }

    @pytest.fixture
    def repository(self) -> CognitoTokenVerifierRepository:
        """テスト用のリポジトリインスタンスを返すフィクスチャ."""
        return CognitoTokenVerifierRepository(
            region="ap-northeast-1",
            user_pool_id="test-pool-id",
            app_client_id="test-client-id",
        )

    @pytest.mark.asyncio
    async def test_jwks_is_fetched_on_first_verify(
        self, repository: CognitoTokenVerifierRepository, mock_jwks: dict[str, Any]
    ) -> None:
        """初回検証時にJWKSを取得する."""
        # Arrange
        with (
            patch.object(
                repository, "_fetch_jwks", new_callable=AsyncMock
            ) as mock_fetch,
            patch("jose.jwt.get_unverified_header") as mock_get_header,
            patch("jose.jwt.decode") as mock_decode,
        ):
            mock_fetch.return_value = mock_jwks
            mock_get_header.return_value = {"kid": "test-key-id-1"}
            mock_decode.return_value = {"sub": "user123"}

            # Act
            await repository.verify("test-token")

            # Assert
            mock_fetch.assert_called_once()
            assert repository._jwks == mock_jwks
            assert repository._jwks_cached_at is not None

    @pytest.mark.asyncio
    async def test_jwks_cache_is_reused_within_ttl(
        self, repository: CognitoTokenVerifierRepository, mock_jwks: dict[str, Any]
    ) -> None:
        """TTL内ではJWKSキャッシュを再利用する."""
        # Arrange
        with (
            patch.object(
                repository, "_fetch_jwks", new_callable=AsyncMock
            ) as mock_fetch,
            patch("jose.jwt.get_unverified_header") as mock_get_header,
            patch("jose.jwt.decode") as mock_decode,
        ):
            mock_fetch.return_value = mock_jwks
            mock_get_header.return_value = {"kid": "test-key-id-1"}
            mock_decode.return_value = {"sub": "user123"}

            # Act - 初回検証
            await repository.verify("test-token-1")
            # Act - 2回目の検証（TTL内）
            await repository.verify("test-token-2")

            # Assert - 初回のみJWKS取得が呼ばれる
            assert mock_fetch.call_count == 1

    @pytest.mark.asyncio
    async def test_jwks_is_refreshed_after_ttl_expires(
        self, repository: CognitoTokenVerifierRepository, mock_jwks: dict[str, Any]
    ) -> None:
        """TTL期限切れ後にJWKSを再取得する."""
        # Arrange
        with (
            patch.object(
                repository, "_fetch_jwks", new_callable=AsyncMock
            ) as mock_fetch,
            patch("jose.jwt.get_unverified_header") as mock_get_header,
            patch("jose.jwt.decode") as mock_decode,
        ):
            mock_fetch.return_value = mock_jwks
            mock_get_header.return_value = {"kid": "test-key-id-1"}
            mock_decode.return_value = {"sub": "user123"}

            # Act - 初回検証
            await repository.verify("test-token-1")

            # TTL期限切れをシミュレート
            repository._jwks_cached_at = time.time() - (JWKS_CACHE_TTL + 1)

            # Act - 2回目の検証（TTL期限切れ後）
            await repository.verify("test-token-2")

            # Assert - 2回JWKSが取得される
            assert mock_fetch.call_count == 2

    @pytest.mark.asyncio
    async def test_jwks_is_refreshed_when_kid_not_found(
        self, repository: CognitoTokenVerifierRepository, mock_jwks: dict[str, Any]
    ) -> None:
        """kidがキャッシュに存在しない場合にJWKSを再取得する（フォールバック機構）."""
        # Arrange
        new_jwks = {
            "keys": [
                {
                    "kid": "new-key-id",
                    "kty": "RSA",
                    "use": "sig",
                    "n": "new-n-value",
                    "e": "AQAB",
                }
            ]
        }

        with (
            patch.object(
                repository, "_fetch_jwks", new_callable=AsyncMock
            ) as mock_fetch,
            patch("jose.jwt.get_unverified_header") as mock_get_header,
            patch("jose.jwt.decode") as mock_decode,
        ):
            # 再取得時に新しいキーを返す
            mock_fetch.side_effect = [new_jwks]
            mock_get_header.return_value = {"kid": "new-key-id"}
            mock_decode.return_value = {"sub": "user123"}

            # Act - 初回検証（古いJWKSをキャッシュ）
            repository._jwks = mock_jwks
            repository._jwks_cached_at = time.time()

            # Act - 新しいkidで検証
            await repository.verify("test-token-with-new-kid")

            # Assert - JWKSが再取得される
            assert mock_fetch.call_count == 1
            assert repository._jwks == new_jwks

    @pytest.mark.asyncio
    async def test_verify_raises_error_when_kid_not_found_even_after_refresh(
        self, repository: CognitoTokenVerifierRepository, mock_jwks: dict[str, Any]
    ) -> None:
        """kidがリフレッシュ後も見つからない場合にエラーを発生させる."""
        # Arrange
        with (
            patch.object(
                repository, "_fetch_jwks", new_callable=AsyncMock
            ) as mock_fetch,
            patch("jose.jwt.get_unverified_header") as mock_get_header,
        ):
            mock_fetch.return_value = mock_jwks
            mock_get_header.return_value = {"kid": "non-existent-kid"}

            # Act & Assert
            with pytest.raises(ErrInvalidToken) as exc_info:
                await repository.verify("test-token")

            assert "Unable to find key with kid 'non-existent-kid'" in str(
                exc_info.value
            )

    @pytest.mark.asyncio
    async def test_verify_raises_error_when_kid_missing_in_token_header(
        self, repository: CognitoTokenVerifierRepository, mock_jwks: dict[str, Any]
    ) -> None:
        """トークンヘッダーにkidが存在しない場合にエラーを発生させる."""
        # Arrange
        with (
            patch.object(
                repository, "_fetch_jwks", new_callable=AsyncMock
            ) as mock_fetch,
            patch("jose.jwt.get_unverified_header") as mock_get_header,
        ):
            mock_fetch.return_value = mock_jwks
            mock_get_header.return_value = {}  # kidなし

            # Act & Assert
            with pytest.raises(ErrInvalidToken) as exc_info:
                await repository.verify("test-token")

            assert "Token header missing 'kid'" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fetch_jwks_raises_error_on_http_error(
        self, repository: CognitoTokenVerifierRepository
    ) -> None:
        """HTTP取得エラー時にErrJwksFetchFailedを発生させる."""
        # Arrange
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = Exception("Network error")
            mock_client_class.return_value = mock_client

            # Act & Assert
            with pytest.raises(ErrJwksFetchFailed):
                await repository._fetch_jwks()

    def test_is_jwks_expired_returns_true_when_jwks_is_none(
        self, repository: CognitoTokenVerifierRepository
    ) -> None:
        """JWKSがNoneの場合にTrueを返す."""
        # Arrange
        repository._jwks = None
        repository._jwks_cached_at = None

        # Act & Assert
        assert repository._is_jwks_expired() is True

    def test_is_jwks_expired_returns_true_when_cached_at_is_none(
        self, repository: CognitoTokenVerifierRepository, mock_jwks: dict[str, Any]
    ) -> None:
        """キャッシュ時刻がNoneの場合にTrueを返す."""
        # Arrange
        repository._jwks = mock_jwks
        repository._jwks_cached_at = None

        # Act & Assert
        assert repository._is_jwks_expired() is True

    def test_is_jwks_expired_returns_true_when_ttl_exceeded(
        self, repository: CognitoTokenVerifierRepository, mock_jwks: dict[str, Any]
    ) -> None:
        """TTL超過時にTrueを返す."""
        # Arrange
        repository._jwks = mock_jwks
        repository._jwks_cached_at = time.time() - (JWKS_CACHE_TTL + 1)

        # Act & Assert
        assert repository._is_jwks_expired() is True

    def test_is_jwks_expired_returns_false_when_within_ttl(
        self, repository: CognitoTokenVerifierRepository, mock_jwks: dict[str, Any]
    ) -> None:
        """TTL内の場合にFalseを返す."""
        # Arrange
        repository._jwks = mock_jwks
        repository._jwks_cached_at = time.time()

        # Act & Assert
        assert repository._is_jwks_expired() is False

    def test_find_signing_key_returns_matching_key(
        self, repository: CognitoTokenVerifierRepository, mock_jwks: dict[str, Any]
    ) -> None:
        """一致するkidの鍵を返す."""
        # Arrange
        repository._jwks = mock_jwks

        # Act
        key = repository._find_signing_key("test-key-id-1")

        # Assert
        assert key is not None
        assert key["kid"] == "test-key-id-1"

    def test_find_signing_key_returns_none_when_kid_not_found(
        self, repository: CognitoTokenVerifierRepository, mock_jwks: dict[str, Any]
    ) -> None:
        """kidが見つからない場合にNoneを返す."""
        # Arrange
        repository._jwks = mock_jwks

        # Act
        key = repository._find_signing_key("non-existent-kid")

        # Assert
        assert key is None

    def test_find_signing_key_returns_none_when_jwks_is_none(
        self, repository: CognitoTokenVerifierRepository
    ) -> None:
        """JWKSがNoneの場合にNoneを返す."""
        # Arrange
        repository._jwks = None

        # Act
        key = repository._find_signing_key("test-key-id-1")

        # Assert
        assert key is None
