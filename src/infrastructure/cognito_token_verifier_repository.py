# 絶対厳守：編集前に必ずAI実装ルールを読む

import asyncio
import logging
import time
from typing import Any, cast

import aiohttp
from jose import JWTError, ExpiredSignatureError
from jose import jwt as jose_jwt

from domain.lgtm_image_errors import (
    ErrExpiredToken,
    ErrInvalidToken,
    ErrJwksFetchFailed,
)
from domain.repository.token_verifier_repository_interface import (
    TokenVerifierRepositoryInterface,
)

logger = logging.getLogger(__name__)

# JWKSキャッシュのTTL（秒）: 24時間
JWKS_CACHE_TTL = 86400


def _build_cognito_jwks_url(region: str, user_pool_id: str) -> str:
    return f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"


def _build_cognito_issuer(region: str, user_pool_id: str) -> str:
    return f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"


class CognitoTokenVerifierRepository(TokenVerifierRepositoryInterface):
    def __init__(self, region: str, user_pool_id: str, app_client_id: str) -> None:
        self.region = region
        self.user_pool_id = user_pool_id
        self.app_client_id = app_client_id
        self.keys_url = _build_cognito_jwks_url(region, user_pool_id)
        self.expected_issuer = _build_cognito_issuer(region, user_pool_id)
        self._jwks: dict[str, Any] | None = None
        self._jwks_cached_at: float | None = None
        self._jwks_lock: asyncio.Lock | None = None

    def _ensure_lock(self) -> asyncio.Lock:
        """Lockを遅延初期化して取得（実行中のイベントループ内で作成）"""
        if self._jwks_lock is None:
            self._jwks_lock = asyncio.Lock()
        return self._jwks_lock

    def _is_jwks_expired(self) -> bool:
        """JWKSキャッシュが期限切れかどうかを判定"""
        if self._jwks is None or self._jwks_cached_at is None:
            return True
        elapsed = time.time() - self._jwks_cached_at
        return elapsed > JWKS_CACHE_TTL

    async def _refresh_jwks(self) -> None:
        """JWKSを取得してキャッシュを更新"""
        self._jwks = await self._fetch_jwks()
        self._jwks_cached_at = time.time()
        logger.info("JWKS refreshed successfully")

    async def verify(self, token: str) -> dict[str, Any]:
        try:
            # JWKSを取得またはリフレッシュ（TTL期限切れまたは初回）
            if self._is_jwks_expired():
                async with self._ensure_lock():
                    # ロック取得後に再チェック（他のコルーチンが既に取得した可能性）
                    if self._is_jwks_expired():
                        await self._refresh_jwks()

            # トークンのヘッダーを取得してkidを確認
            unverified_header = jose_jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise ErrInvalidToken("Token header missing 'kid'")

            # kidに対応する公開鍵を取得
            key = self._find_signing_key(kid)

            # フォールバック機構: kidが見つからない場合はJWKSを再取得
            if not key:
                logger.warning(
                    f"Key with kid '{kid}' not found in cache, refreshing JWKS"
                )
                async with self._ensure_lock():
                    # 他のコルーチンが既に更新していないか確認
                    key = self._find_signing_key(kid)
                    if not key:
                        await self._refresh_jwks()
                        key = self._find_signing_key(kid)
                        if not key:
                            raise ErrInvalidToken(
                                f"Unable to find key with kid '{kid}' even after refresh"
                            )

            # トークンを検証
            payload = jose_jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.app_client_id,
                issuer=self.expected_issuer,
                options={"verify_aud": True, "verify_iss": True},
            )

            logger.info("Token verified successfully")
            return payload

        except ExpiredSignatureError:
            logger.warning("Token has expired")
            raise ErrExpiredToken("Token has expired")
        except JWTError as e:
            logger.error(f"Invalid token: {e}")
            raise ErrInvalidToken(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise ErrInvalidToken(f"Token verification failed: {str(e)}")

    async def _fetch_jwks(self) -> dict[str, Any]:
        try:
            timeout = aiohttp.ClientTimeout(total=10.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.keys_url) as response:
                    response.raise_for_status()
                    return cast(dict[str, Any], await response.json())
        except aiohttp.ClientError as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            raise ErrJwksFetchFailed("Failed to fetch JWKS")
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            raise ErrJwksFetchFailed("Failed to fetch JWKS")

    def _find_signing_key(self, kid: str) -> dict[str, Any] | None:
        if not self._jwks:
            return None

        keys = self._jwks.get("keys", [])
        for key in keys:
            if key.get("kid") == kid:
                return cast(dict[str, Any], key)

        return None
