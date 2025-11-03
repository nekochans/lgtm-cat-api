# 絶対厳守:編集前に必ずAI実装ルールを読む

import aiohttp
from magika import Magika
from urllib.parse import urlsplit, urlunsplit

from domain.image_format import ALLOWED_IMAGE_MIME_TYPES
from domain.lgtm_image_errors import (
    ErrImageFetchFailed,
    ErrInvalidUrl,
    ErrUrlNotAccessible,
)
from domain.repository.image_fetch_repository_interface import (
    FetchedImage,
    ImageFetchRepositoryInterface,
)
from infrastructure.validator.url_validator import validate_allowed_domain
from log.logger import get_logger

logger = get_logger(__name__)


def _sanitize_url_for_logging(url: str) -> str:
    parsed = urlsplit(url)
    # クエリ文字列とフラグメントを空にして再構築
    sanitized = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    return sanitized


class HttpImageFetchRepository(ImageFetchRepositoryInterface):
    def __init__(self, timeout: int, max_size: int, allowed_domain: str) -> None:
        self._timeout = timeout
        self._max_size = max_size
        self._allowed_domain = allowed_domain
        self._magika = Magika()

    async def fetch_image(self, url: str) -> FetchedImage:
        # クエリパラメータを除去したログ出力用URL（機密情報保護）
        sanitized_url = _sanitize_url_for_logging(url)

        # SSRF対策のURL検証(許可されたドメインのみ許可)
        try:
            validate_allowed_domain(url, self._allowed_domain)
        except ErrInvalidUrl:
            logger.warning(f"Invalid URL detected: {sanitized_url}")
            raise

        logger.info(f"Fetching image from URL: {sanitized_url}")

        try:
            timeout = aiohttp.ClientTimeout(total=self._timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # リダイレクトを許可しない方針 + 圧縮を無効化
                async with session.get(
                    url, allow_redirects=False, headers={"Accept-Encoding": "identity"}
                ) as response:
                    # リダイレクトが返された場合はエラー
                    if 300 <= response.status < 400:
                        redirect_url = response.headers.get("Location")
                        sanitized_redirect = (
                            _sanitize_url_for_logging(redirect_url)
                            if redirect_url
                            else "(no location)"
                        )
                        logger.warning(
                            f"Blocked redirect from {sanitized_url} to {sanitized_redirect}"
                        )
                        raise ErrUrlNotAccessible(
                            f"Redirect not allowed for URL: {sanitized_url}"
                        )

                    # HTTPステータスコードのチェック（4xx, 5xx）
                    if response.status >= 400:
                        logger.warning(
                            f"HTTP error {response.status} for URL: {sanitized_url}"
                        )
                        raise ErrUrlNotAccessible(
                            f"HTTP error {response.status}: {sanitized_url}"
                        )

                    # Content-Typeの検証(許可された画像形式のみ)
                    content_type = response.headers.get("Content-Type", "")
                    content_main = content_type.split(";")[0].strip().lower()
                    if content_main not in ALLOWED_IMAGE_MIME_TYPES:
                        logger.warning(
                            f"Invalid content type: {content_type} for URL: {sanitized_url}"
                        )
                        raise ErrImageFetchFailed(
                            f"Invalid content type: {content_type}. Expected image format (jpeg, png)"
                        )

                    # Content-Lengthのチェック(サイズ制限)
                    content_length = response.headers.get("Content-Length")
                    if content_length:
                        try:
                            content_length_int = int(content_length)
                            # 非正の値や明らかに無効な値を不正な値として扱う
                            if content_length_int <= 0:
                                logger.warning(
                                    f"Malformed Content-Length header (non-positive value: {content_length}) for URL: {sanitized_url}. Skipping size check."
                                )
                            elif content_length_int > self._max_size:
                                logger.warning(
                                    f"Image size {content_length_int} exceeds max size {self._max_size} for URL: {sanitized_url}"
                                )
                                raise ErrImageFetchFailed(
                                    f"Image size exceeds maximum allowed size: {self._max_size} bytes"
                                )
                        except ValueError:
                            logger.warning(
                                f"Malformed Content-Length header (invalid format: {content_length}) for URL: {sanitized_url}. Skipping size check."
                            )

                    # 画像データの読み込み(サイズ制限付き)
                    image_data = bytearray()
                    async for chunk in response.content.iter_chunked(8192):
                        image_data.extend(chunk)
                        if len(image_data) > self._max_size:
                            logger.warning(
                                f"Image size exceeds max size {self._max_size} during download for URL: {sanitized_url}"
                            )
                            raise ErrImageFetchFailed(
                                f"Image size exceeds maximum allowed size: {self._max_size} bytes"
                            )

                    # Magikaによる実際のファイル内容の検証
                    image_bytes = bytes(image_data)
                    try:
                        result = self._magika.identify_bytes(image_bytes)
                        detected_mime = result.output.mime_type
                    except Exception as e:
                        logger.warning(
                            f"Magika failed to identify file type for URL {sanitized_url}: {e}"
                        )
                        raise ErrImageFetchFailed(
                            "Unable to determine file type"
                        ) from e

                    if detected_mime not in ALLOWED_IMAGE_MIME_TYPES:
                        logger.warning(
                            f"Invalid file type detected by Magika: {detected_mime} for URL: {sanitized_url}"
                        )
                        raise ErrImageFetchFailed(
                            f"Invalid file type: {detected_mime}. Expected image format (jpeg, png)"
                        )

                    logger.info(
                        f"Successfully fetched and validated image ({len(image_bytes)} bytes, type: {detected_mime}) from URL: {sanitized_url}"
                    )
                    return {"data": image_bytes, "mime_type": detected_mime}

        except aiohttp.ClientError as e:
            logger.error(f"Failed to fetch image from URL {sanitized_url}: {e}")
            raise ErrImageFetchFailed(f"Failed to fetch image: {e}") from e
        except ErrUrlNotAccessible:
            raise
        except ErrImageFetchFailed:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while fetching image from URL {sanitized_url}: {e}"
            )
            raise ErrImageFetchFailed(f"Unexpected error: {e}") from e
