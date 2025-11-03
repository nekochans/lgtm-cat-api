# 絶対厳守：編集前に必ずAI実装ルールを読む
"""HttpImageFetchRepositoryのテスト."""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from domain.lgtm_image_errors import (
    ErrImageFetchFailed,
    ErrInvalidUrl,
    ErrUrlNotAccessible,
)
from infrastructure.repository.http_image_fetch_repository import (
    HttpImageFetchRepository,
)


class TestHttpImageFetchRepository:
    # テスト用の許可ドメイン
    ALLOWED_DOMAIN = "test-bucket.r2.cloudflarestorage.com"

    @pytest.fixture
    def repository(self) -> HttpImageFetchRepository:
        """テスト用のリポジトリインスタンスを生成."""
        return HttpImageFetchRepository(
            timeout=30,
            max_size=10 * 1024 * 1024,
            allowed_domain=self.ALLOWED_DOMAIN,
        )

    def _create_mock_session(self, mock_get: AsyncMock) -> MagicMock:
        """aiohttpセッションのモックを作成する."""
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_get)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        return mock_session

    def _create_mock_response(
        self,
        status: int,
        headers: dict[str, str] | None = None,
        content: MagicMock | None = None,
    ) -> MagicMock:
        """HTTPレスポンスのモックを作成する."""
        mock_response = MagicMock()
        mock_response.status = status
        mock_response.headers = headers or {}
        mock_response.raise_for_status = MagicMock()
        if content:
            mock_response.content = content
        return mock_response

    def _create_mock_magika_result(self, mime_type: str) -> MagicMock:
        """Magika結果のモックを作成する."""
        mock_magika_result = MagicMock()
        mock_magika_output = MagicMock()
        mock_magika_output.mime_type = mime_type
        mock_magika_result.output = mock_magika_output
        return mock_magika_result

    @pytest.mark.asyncio
    async def test_fetch_image_success(
        self, repository: HttpImageFetchRepository
    ) -> None:
        """正常系: 画像の取得に成功し、URL検証が呼び出されることを確認する."""
        # Arrange
        url = "https://test-bucket.r2.cloudflarestorage.com/image.jpg"
        expected_data = b"fake image data"

        async def mock_iter_chunked(size: int) -> AsyncIterator[bytes]:
            yield expected_data

        mock_content = MagicMock()
        mock_content.iter_chunked = mock_iter_chunked

        mock_response = self._create_mock_response(
            status=200,
            headers={"Content-Type": "image/jpeg", "Content-Length": "15"},
            content=mock_content,
        )

        mock_get = AsyncMock(return_value=mock_response)
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        mock_magika_result = self._create_mock_magika_result("image/jpeg")

        # Act
        with patch(
            "infrastructure.repository.http_image_fetch_repository.validate_allowed_domain"
        ) as mock_validate:
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = self._create_mock_session(mock_get)
                mock_session_class.return_value = mock_session

                with patch.object(
                    repository._magika,
                    "identify_bytes",
                    return_value=mock_magika_result,
                ):
                    result = await repository.fetch_image(url)

        # Assert
        assert result["data"] == expected_data
        assert result["mime_type"] == "image/jpeg"
        mock_session.get.assert_called_once_with(
            url, allow_redirects=False, headers={"Accept-Encoding": "identity"}
        )
        mock_validate.assert_called_once_with(url, self.ALLOWED_DOMAIN)

    @pytest.mark.asyncio
    async def test_fetch_image_propagates_validation_error(
        self, repository: HttpImageFetchRepository
    ) -> None:
        """異常系: validate_allowed_domain()の例外が正しく伝播することを確認する."""
        # Arrange
        url = "http://localhost/image.jpg"

        # Act & Assert
        with patch(
            "infrastructure.repository.http_image_fetch_repository.validate_allowed_domain"
        ) as mock_validate:
            mock_validate.side_effect = ErrInvalidUrl(
                "Access to localhost is not allowed"
            )

            with pytest.raises(ErrInvalidUrl) as exc_info:
                await repository.fetch_image(url)

            assert "localhost" in str(exc_info.value).lower()
            mock_validate.assert_called_once_with(url, self.ALLOWED_DOMAIN)

    @pytest.mark.asyncio
    async def test_fetch_image_http_404_not_found(
        self, repository: HttpImageFetchRepository
    ) -> None:
        """異常系: HTTP 404エラーの場合、ErrUrlNotAccessibleを発生させる."""
        # Arrange
        url = "https://test-bucket.r2.cloudflarestorage.com/not-found.jpg"

        mock_response = self._create_mock_response(status=404)

        mock_get = AsyncMock(return_value=mock_response)
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        # Act & Assert
        with patch(
            "infrastructure.repository.http_image_fetch_repository.validate_allowed_domain"
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = self._create_mock_session(mock_get)
                mock_session_class.return_value = mock_session

                with pytest.raises(ErrUrlNotAccessible) as exc_info:
                    await repository.fetch_image(url)

        error_msg = str(exc_info.value)
        assert "404" in error_msg or "not found" in error_msg.lower()
        assert url in error_msg

    @pytest.mark.asyncio
    async def test_fetch_image_invalid_content_type(
        self, repository: HttpImageFetchRepository
    ) -> None:
        """異常系: Content-Typeが画像でない場合、ErrImageFetchFailedを発生させる."""
        # Arrange
        url = "https://test-bucket.r2.cloudflarestorage.com/document.pdf"

        mock_response = self._create_mock_response(
            status=200, headers={"Content-Type": "application/pdf"}
        )

        mock_get = AsyncMock(return_value=mock_response)
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        # Act & Assert
        with patch(
            "infrastructure.repository.http_image_fetch_repository.validate_allowed_domain"
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = self._create_mock_session(mock_get)
                mock_session_class.return_value = mock_session

                with pytest.raises(ErrImageFetchFailed) as exc_info:
                    await repository.fetch_image(url)

        error_msg = str(exc_info.value)
        assert "content type" in error_msg.lower() or "invalid" in error_msg.lower()
        assert "application/pdf" in error_msg

    @pytest.mark.asyncio
    async def test_fetch_image_exceeds_max_size_by_content_length(self) -> None:
        """異常系: Content-Lengthが最大サイズを超える場合、ErrImageFetchFailedを発生させる."""
        # Arrange
        url = "https://test-bucket.r2.cloudflarestorage.com/large-image.jpg"
        max_size = 1000  # 1KB

        repository = HttpImageFetchRepository(
            timeout=30, max_size=max_size, allowed_domain=self.ALLOWED_DOMAIN
        )

        mock_response = self._create_mock_response(
            status=200,
            headers={"Content-Type": "image/jpeg", "Content-Length": "2000"},
        )

        mock_get = AsyncMock(return_value=mock_response)
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        # Act & Assert
        with patch(
            "infrastructure.repository.http_image_fetch_repository.validate_allowed_domain"
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = self._create_mock_session(mock_get)
                mock_session_class.return_value = mock_session

                with pytest.raises(ErrImageFetchFailed) as exc_info:
                    await repository.fetch_image(url)

        error_msg = str(exc_info.value)
        assert "exceeds" in error_msg.lower() or "too large" in error_msg.lower()
        assert "2000" in error_msg or "1000" in error_msg

    @pytest.mark.asyncio
    async def test_fetch_image_exceeds_max_size_during_download(self) -> None:
        """異常系: ダウンロード中に最大サイズを超える場合、ErrImageFetchFailedを発生させる."""
        # Arrange
        url = "https://test-bucket.r2.cloudflarestorage.com/image.jpg"
        max_size = 10  # 10バイト

        repository = HttpImageFetchRepository(
            timeout=30, max_size=max_size, allowed_domain=self.ALLOWED_DOMAIN
        )

        large_data = b"x" * 20  # 20バイト（max_sizeを超える）

        async def mock_iter_chunked(size: int) -> AsyncIterator[bytes]:
            yield large_data

        mock_content = MagicMock()
        mock_content.iter_chunked = mock_iter_chunked

        mock_response = self._create_mock_response(
            status=200, headers={"Content-Type": "image/jpeg"}, content=mock_content
        )

        mock_get = AsyncMock(return_value=mock_response)
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        # Act & Assert
        with patch(
            "infrastructure.repository.http_image_fetch_repository.validate_allowed_domain"
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = self._create_mock_session(mock_get)
                mock_session_class.return_value = mock_session

                with pytest.raises(ErrImageFetchFailed) as exc_info:
                    await repository.fetch_image(url)

        error_msg = str(exc_info.value)
        assert "exceeds" in error_msg.lower() or "too large" in error_msg.lower()

    @pytest.mark.asyncio
    async def test_fetch_image_client_error(
        self, repository: HttpImageFetchRepository
    ) -> None:
        """異常系: aiohttpのClientErrorが発生した場合、ErrImageFetchFailedを発生させる."""
        # Arrange
        url = "https://test-bucket.r2.cloudflarestorage.com/image.jpg"

        # Act & Assert
        with patch(
            "infrastructure.repository.http_image_fetch_repository.validate_allowed_domain"
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = MagicMock()
                mock_session.__aenter__ = AsyncMock(
                    side_effect=aiohttp.ClientError("Connection failed")
                )
                mock_session.__aexit__ = AsyncMock(return_value=None)
                mock_session_class.return_value = mock_session

                with pytest.raises(ErrImageFetchFailed) as exc_info:
                    await repository.fetch_image(url)

        error_msg = str(exc_info.value)
        assert "failed" in error_msg.lower() or "error" in error_msg.lower()

    @pytest.mark.asyncio
    async def test_fetch_image_http_500_server_error(
        self, repository: HttpImageFetchRepository
    ) -> None:
        """異常系: HTTP 500エラーの場合、ErrUrlNotAccessibleを発生させる."""
        # Arrange
        url = "https://test-bucket.r2.cloudflarestorage.com/error.jpg"

        mock_response = self._create_mock_response(status=500)

        mock_get = AsyncMock(return_value=mock_response)
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        # Act & Assert
        with patch(
            "infrastructure.repository.http_image_fetch_repository.validate_allowed_domain"
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = self._create_mock_session(mock_get)
                mock_session_class.return_value = mock_session

                with pytest.raises(ErrUrlNotAccessible) as exc_info:
                    await repository.fetch_image(url)

        error_msg = str(exc_info.value)
        assert "500" in error_msg
        assert url in error_msg

    @pytest.mark.asyncio
    async def test_fetch_image_invalid_file_type_by_magika(
        self, repository: HttpImageFetchRepository
    ) -> None:
        """異常系: Magikaが不正なファイルタイプを検出した場合、ErrImageFetchFailedを発生させる."""
        # Arrange
        url = "https://test-bucket.r2.cloudflarestorage.com/fake-image.jpg"

        # ヘッダーではimage/jpegだが、実際の内容はPDF
        fake_image_data = b"fake pdf content"

        async def mock_iter_chunked(size: int) -> AsyncIterator[bytes]:
            yield fake_image_data

        mock_content = MagicMock()
        mock_content.iter_chunked = mock_iter_chunked

        mock_response = self._create_mock_response(
            status=200,
            headers={"Content-Type": "image/jpeg", "Content-Length": "16"},
            content=mock_content,
        )

        mock_get = AsyncMock(return_value=mock_response)
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        mock_magika_result = self._create_mock_magika_result("application/pdf")

        # Act & Assert
        with patch(
            "infrastructure.repository.http_image_fetch_repository.validate_allowed_domain"
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = self._create_mock_session(mock_get)
                mock_session_class.return_value = mock_session

                with patch.object(
                    repository._magika,
                    "identify_bytes",
                    return_value=mock_magika_result,
                ):
                    with pytest.raises(ErrImageFetchFailed) as exc_info:
                        await repository.fetch_image(url)

        error_msg = str(exc_info.value)
        assert "file type" in error_msg.lower() or "invalid" in error_msg.lower()
        assert "application/pdf" in error_msg

    @pytest.mark.asyncio
    async def test_fetch_image_timeout(self) -> None:
        """異常系: タイムアウトが発生した場合、ErrImageFetchFailedを発生させる."""
        # Arrange
        url = "https://test-bucket.r2.cloudflarestorage.com/slow-image.jpg"
        timeout = 1  # 短いタイムアウト

        repository = HttpImageFetchRepository(
            timeout=timeout,
            max_size=10 * 1024 * 1024,
            allowed_domain=self.ALLOWED_DOMAIN,
        )

        # Act & Assert
        with patch(
            "infrastructure.repository.http_image_fetch_repository.validate_allowed_domain"
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = MagicMock()
                mock_session.__aenter__ = AsyncMock(
                    side_effect=aiohttp.ServerTimeoutError("Timeout")
                )
                mock_session.__aexit__ = AsyncMock(return_value=None)
                mock_session_class.return_value = mock_session

                with pytest.raises(ErrImageFetchFailed) as exc_info:
                    await repository.fetch_image(url)

        error_msg = str(exc_info.value)
        assert "timeout" in error_msg.lower() or "failed" in error_msg.lower()

    @pytest.mark.asyncio
    async def test_fetch_image_without_content_length_header(
        self, repository: HttpImageFetchRepository
    ) -> None:
        """正常系: Content-Lengthヘッダーが存在しない場合でも、正常に取得できる."""
        # Arrange
        url = "https://test-bucket.r2.cloudflarestorage.com/image.jpg"
        expected_data = b"image data without content-length"

        async def mock_iter_chunked(size: int) -> AsyncIterator[bytes]:
            yield expected_data

        mock_content = MagicMock()
        mock_content.iter_chunked = mock_iter_chunked

        # Content-Lengthヘッダーなし
        mock_response = self._create_mock_response(
            status=200, headers={"Content-Type": "image/jpeg"}, content=mock_content
        )

        mock_get = AsyncMock(return_value=mock_response)
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        mock_magika_result = self._create_mock_magika_result("image/jpeg")

        # Act
        with patch(
            "infrastructure.repository.http_image_fetch_repository.validate_allowed_domain"
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = self._create_mock_session(mock_get)
                mock_session_class.return_value = mock_session

                with patch.object(
                    repository._magika,
                    "identify_bytes",
                    return_value=mock_magika_result,
                ):
                    result = await repository.fetch_image(url)

        # Assert
        assert result["data"] == expected_data
        assert result["mime_type"] == "image/jpeg"

    @pytest.mark.asyncio
    async def test_fetch_image_malformed_content_length_non_numeric(
        self, repository: HttpImageFetchRepository
    ) -> None:
        """正常系: Content-Lengthヘッダーが数値でない場合、警告ログを出力してサイズチェックをスキップし、正常に取得できる."""
        # Arrange
        url = "https://test-bucket.r2.cloudflarestorage.com/image.jpg"
        expected_data = b"image data with malformed content-length"

        async def mock_iter_chunked(size: int) -> AsyncIterator[bytes]:
            yield expected_data

        mock_content = MagicMock()
        mock_content.iter_chunked = mock_iter_chunked

        # Content-Lengthヘッダーが不正な形式(数値でない)
        mock_response = self._create_mock_response(
            status=200,
            headers={"Content-Type": "image/jpeg", "Content-Length": "invalid"},
            content=mock_content,
        )

        mock_get = AsyncMock(return_value=mock_response)
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        mock_magika_result = self._create_mock_magika_result("image/jpeg")

        # Act
        with patch(
            "infrastructure.repository.http_image_fetch_repository.validate_allowed_domain"
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = self._create_mock_session(mock_get)
                mock_session_class.return_value = mock_session

                with patch.object(
                    repository._magika,
                    "identify_bytes",
                    return_value=mock_magika_result,
                ):
                    result = await repository.fetch_image(url)

        # Assert
        assert result["data"] == expected_data
        assert result["mime_type"] == "image/jpeg"

    @pytest.mark.asyncio
    async def test_fetch_image_malformed_content_length_zero(
        self, repository: HttpImageFetchRepository
    ) -> None:
        """正常系: Content-Lengthヘッダーがゼロの場合、警告ログを出力してサイズチェックをスキップし、正常に取得できる."""
        # Arrange
        url = "https://test-bucket.r2.cloudflarestorage.com/image.jpg"
        expected_data = b"image data with zero content-length"

        async def mock_iter_chunked(size: int) -> AsyncIterator[bytes]:
            yield expected_data

        mock_content = MagicMock()
        mock_content.iter_chunked = mock_iter_chunked

        # Content-Lengthヘッダーが0(非正の値)
        mock_response = self._create_mock_response(
            status=200,
            headers={"Content-Type": "image/jpeg", "Content-Length": "0"},
            content=mock_content,
        )

        mock_get = AsyncMock(return_value=mock_response)
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        mock_magika_result = self._create_mock_magika_result("image/jpeg")

        # Act
        with patch(
            "infrastructure.repository.http_image_fetch_repository.validate_allowed_domain"
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = self._create_mock_session(mock_get)
                mock_session_class.return_value = mock_session

                with patch.object(
                    repository._magika,
                    "identify_bytes",
                    return_value=mock_magika_result,
                ):
                    result = await repository.fetch_image(url)

        # Assert
        assert result["data"] == expected_data
        assert result["mime_type"] == "image/jpeg"

    @pytest.mark.asyncio
    async def test_fetch_image_malformed_content_length_negative(
        self, repository: HttpImageFetchRepository
    ) -> None:
        """正常系: Content-Lengthヘッダーが負の値の場合、警告ログを出力してサイズチェックをスキップし、正常に取得できる."""
        # Arrange
        url = "https://test-bucket.r2.cloudflarestorage.com/image.jpg"
        expected_data = b"image data with negative content-length"

        async def mock_iter_chunked(size: int) -> AsyncIterator[bytes]:
            yield expected_data

        mock_content = MagicMock()
        mock_content.iter_chunked = mock_iter_chunked

        # Content-Lengthヘッダーが負の値(非正の値)
        mock_response = self._create_mock_response(
            status=200,
            headers={"Content-Type": "image/jpeg", "Content-Length": "-100"},
            content=mock_content,
        )

        mock_get = AsyncMock(return_value=mock_response)
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        mock_magika_result = self._create_mock_magika_result("image/jpeg")

        # Act
        with patch(
            "infrastructure.repository.http_image_fetch_repository.validate_allowed_domain"
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = self._create_mock_session(mock_get)
                mock_session_class.return_value = mock_session

                with patch.object(
                    repository._magika,
                    "identify_bytes",
                    return_value=mock_magika_result,
                ):
                    result = await repository.fetch_image(url)

        # Assert
        assert result["data"] == expected_data
        assert result["mime_type"] == "image/jpeg"

    @pytest.mark.asyncio
    async def test_fetch_image_multiple_chunks(
        self, repository: HttpImageFetchRepository
    ) -> None:
        """正常系: 複数チャンクに分割されたダウンロードで正常に取得できる."""
        # Arrange
        url = "https://test-bucket.r2.cloudflarestorage.com/image.jpg"
        chunk1 = b"first chunk "
        chunk2 = b"second chunk "
        chunk3 = b"third chunk"
        expected_data = chunk1 + chunk2 + chunk3

        async def mock_iter_chunked(size: int) -> AsyncIterator[bytes]:
            yield chunk1
            yield chunk2
            yield chunk3

        mock_content = MagicMock()
        mock_content.iter_chunked = mock_iter_chunked

        mock_response = self._create_mock_response(
            status=200,
            headers={
                "Content-Type": "image/png",
                "Content-Length": str(len(expected_data)),
            },
            content=mock_content,
        )

        mock_get = AsyncMock(return_value=mock_response)
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        mock_magika_result = self._create_mock_magika_result("image/png")

        # Act
        with patch(
            "infrastructure.repository.http_image_fetch_repository.validate_allowed_domain"
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = self._create_mock_session(mock_get)
                mock_session_class.return_value = mock_session

                with patch.object(
                    repository._magika,
                    "identify_bytes",
                    return_value=mock_magika_result,
                ):
                    result = await repository.fetch_image(url)

        # Assert
        assert result["data"] == expected_data
        assert result["mime_type"] == "image/png"

    @pytest.mark.asyncio
    async def test_fetch_image_multiple_chunks_exceeds_max_size(self) -> None:
        """異常系: 複数チャンクの合計がmax_sizeを超える場合、エラーを発生させる."""
        # Arrange
        url = "https://test-bucket.r2.cloudflarestorage.com/image.jpg"
        max_size = 20  # 20バイト

        repository = HttpImageFetchRepository(
            timeout=30, max_size=max_size, allowed_domain=self.ALLOWED_DOMAIN
        )

        chunk1 = b"first "  # 6バイト
        chunk2 = b"second "  # 7バイト
        chunk3 = b"third chunk"  # 11バイト（合計24バイト、max_size超過）

        async def mock_iter_chunked(size: int) -> AsyncIterator[bytes]:
            yield chunk1
            yield chunk2
            yield chunk3

        mock_content = MagicMock()
        mock_content.iter_chunked = mock_iter_chunked

        mock_response = self._create_mock_response(
            status=200, headers={"Content-Type": "image/jpeg"}, content=mock_content
        )

        mock_get = AsyncMock(return_value=mock_response)
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        # Act & Assert
        with patch(
            "infrastructure.repository.http_image_fetch_repository.validate_allowed_domain"
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = self._create_mock_session(mock_get)
                mock_session_class.return_value = mock_session

                with pytest.raises(ErrImageFetchFailed) as exc_info:
                    await repository.fetch_image(url)

        error_msg = str(exc_info.value)
        assert "exceeds" in error_msg.lower() or "too large" in error_msg.lower()

    @pytest.mark.asyncio
    async def test_fetch_image_webp_format_rejected(
        self, repository: HttpImageFetchRepository
    ) -> None:
        """異常系: WebP形式の画像はMagikaで検出され拒否される."""
        # Arrange
        url = "https://test-bucket.r2.cloudflarestorage.com/image.webp"
        webp_data = b"fake webp data"

        async def mock_iter_chunked(size: int) -> AsyncIterator[bytes]:
            yield webp_data

        mock_content = MagicMock()
        mock_content.iter_chunked = mock_iter_chunked

        mock_response = self._create_mock_response(
            status=200,
            headers={
                "Content-Type": "image/webp",
                "Content-Length": str(len(webp_data)),
            },
            content=mock_content,
        )

        mock_get = AsyncMock(return_value=mock_response)
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        # WebPはJPEGとPNGのみ許可されているため拒否される
        mock_magika_result = self._create_mock_magika_result("image/webp")

        # Act & Assert
        with patch(
            "infrastructure.repository.http_image_fetch_repository.validate_allowed_domain"
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = self._create_mock_session(mock_get)
                mock_session_class.return_value = mock_session

                with patch.object(
                    repository._magika,
                    "identify_bytes",
                    return_value=mock_magika_result,
                ):
                    with pytest.raises(ErrImageFetchFailed) as exc_info:
                        await repository.fetch_image(url)

        error_msg = str(exc_info.value)
        assert "file type" in error_msg.lower() or "invalid" in error_msg.lower()
        assert "image/webp" in error_msg

    @pytest.mark.asyncio
    async def test_fetch_image_http_403_forbidden(
        self, repository: HttpImageFetchRepository
    ) -> None:
        """異常系: HTTP 403 Forbiddenエラーの場合、ErrUrlNotAccessibleを発生させる."""
        # Arrange
        url = "https://test-bucket.r2.cloudflarestorage.com/forbidden.jpg"

        mock_response = self._create_mock_response(status=403)

        mock_get = AsyncMock(return_value=mock_response)
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        # Act & Assert
        with patch(
            "infrastructure.repository.http_image_fetch_repository.validate_allowed_domain"
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = self._create_mock_session(mock_get)
                mock_session_class.return_value = mock_session

                with pytest.raises(ErrUrlNotAccessible) as exc_info:
                    await repository.fetch_image(url)

        error_msg = str(exc_info.value)
        assert "403" in error_msg
        assert url in error_msg

    @pytest.mark.asyncio
    async def test_fetch_image_redirect_blocked(
        self, repository: HttpImageFetchRepository
    ) -> None:
        """異常系: リダイレクト(3xx)レスポンスの場合、ErrUrlNotAccessibleを発生させる."""
        # Arrange
        url = "https://test-bucket.r2.cloudflarestorage.com/redirect-image.jpg"
        redirect_url = "https://different-domain.com/image.jpg"

        mock_response = self._create_mock_response(
            status=301, headers={"Location": redirect_url}
        )

        mock_get = AsyncMock(return_value=mock_response)
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        # Act & Assert
        with patch(
            "infrastructure.repository.http_image_fetch_repository.validate_allowed_domain"
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = self._create_mock_session(mock_get)
                mock_session_class.return_value = mock_session

                with pytest.raises(ErrUrlNotAccessible) as exc_info:
                    await repository.fetch_image(url)

        error_msg = str(exc_info.value)
        assert "redirect" in error_msg.lower()
        assert url in error_msg
