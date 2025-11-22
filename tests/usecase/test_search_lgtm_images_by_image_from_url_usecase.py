# 絶対厳守：編集前に必ずAI実装ルールを読む

from unittest.mock import AsyncMock

import pytest

from domain.lgtm_image_errors import (
    ErrImageFetchFailed,
    ErrInvalidImageExtension,
    ErrInvalidUrl,
    ErrUrlNotAccessible,
)
from domain.lgtm_image_search import (
    DEFAULT_SEARCH_MAX_RESULTS,
    LgtmImageSearchResult,
)
from usecase.search_lgtm_images_by_image_from_url_usecase import (
    SearchLgtmImagesByImageFromUrlUsecase,
)


class TestSearchLgtmImagesByImageFromUrlUsecase:
    """SearchLgtmImagesByImageFromUrlUsecaseの統合テスト.

    署名付きURLから画像を取得し、類似画像検索を実行する。
    Repository層のモックを使用してテストを実施する。
    """

    @pytest.mark.asyncio
    async def test_execute_success_with_valid_url(self) -> None:
        """正常系: 署名付きURLから画像を取得して検索成功."""
        # Arrange
        mock_image_fetch_repo = AsyncMock()
        mock_search_repo = AsyncMock()

        # 画像取得のモック
        mock_image_fetch_repo.fetch_image.return_value = {
            "data": b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR...",
            "mime_type": "image/png",
        }

        # 検索結果のモック
        mock_results: list[LgtmImageSearchResult] = [
            {
                "id": "1",
                "url": "https://example.com/image1.webp",
                "similarity_score": 0.95,
            },
            {
                "id": "2",
                "url": "https://example.com/image2.webp",
                "similarity_score": 0.87,
            },
        ]
        mock_search_repo.search_by_image.return_value = mock_results

        image_url = "https://allowed-bucket.r2.cloudflarestorage.com/image.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256"

        # Act
        result = await SearchLgtmImagesByImageFromUrlUsecase.execute(
            image_fetch_repository=mock_image_fetch_repo,
            search_repository=mock_search_repo,
            image_url=image_url,
        )

        # Assert
        assert len(result) == 2
        assert result == mock_results
        mock_image_fetch_repo.fetch_image.assert_called_once_with(image_url)
        mock_search_repo.search_by_image.assert_called_once()
        # base64エンコードされた画像データが渡されることを確認
        call_args = mock_search_repo.search_by_image.call_args
        assert call_args.kwargs["image_extension"] == ".png"
        assert call_args.kwargs["max_results"] == DEFAULT_SEARCH_MAX_RESULTS

    @pytest.mark.asyncio
    async def test_execute_invalid_url(self) -> None:
        """異常系: 無効なURLの場合、ErrInvalidUrlが発生する."""
        # Arrange
        mock_image_fetch_repo = AsyncMock()
        mock_search_repo = AsyncMock()

        mock_image_fetch_repo.fetch_image.side_effect = ErrInvalidUrl(
            "Invalid URL format"
        )

        image_url = "invalid-url"

        # Act & Assert
        with pytest.raises(ErrInvalidUrl):
            await SearchLgtmImagesByImageFromUrlUsecase.execute(
                image_fetch_repository=mock_image_fetch_repo,
                search_repository=mock_search_repo,
                image_url=image_url,
            )

        mock_image_fetch_repo.fetch_image.assert_called_once_with(image_url)
        mock_search_repo.search_by_image.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_url_not_accessible(self) -> None:
        """異常系: URLにアクセスできない場合、ErrUrlNotAccessibleが発生する."""
        # Arrange
        mock_image_fetch_repo = AsyncMock()
        mock_search_repo = AsyncMock()

        mock_image_fetch_repo.fetch_image.side_effect = ErrUrlNotAccessible(
            "URL is not accessible"
        )

        image_url = "https://disallowed-domain.com/image.jpg"

        # Act & Assert
        with pytest.raises(ErrUrlNotAccessible):
            await SearchLgtmImagesByImageFromUrlUsecase.execute(
                image_fetch_repository=mock_image_fetch_repo,
                search_repository=mock_search_repo,
                image_url=image_url,
            )

        mock_image_fetch_repo.fetch_image.assert_called_once_with(image_url)
        mock_search_repo.search_by_image.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_image_fetch_failed(self) -> None:
        """異常系: 画像取得失敗の場合、ErrImageFetchFailedが発生する."""
        # Arrange
        mock_image_fetch_repo = AsyncMock()
        mock_search_repo = AsyncMock()

        mock_image_fetch_repo.fetch_image.side_effect = ErrImageFetchFailed(
            "Failed to fetch image"
        )

        image_url = "https://example.com/broken-image.jpg"

        # Act & Assert
        with pytest.raises(ErrImageFetchFailed):
            await SearchLgtmImagesByImageFromUrlUsecase.execute(
                image_fetch_repository=mock_image_fetch_repo,
                search_repository=mock_search_repo,
                image_url=image_url,
            )

        mock_image_fetch_repo.fetch_image.assert_called_once_with(image_url)
        mock_search_repo.search_by_image.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_invalid_image_extension(self) -> None:
        """異常系: 無効な画像形式の場合、ErrInvalidImageExtensionが発生する."""
        # Arrange
        mock_image_fetch_repo = AsyncMock()
        mock_search_repo = AsyncMock()

        # 無効なMIMEタイプを返す
        mock_image_fetch_repo.fetch_image.return_value = {
            "data": b"invalid data",
            "mime_type": "application/pdf",  # PDFは許可されていない
        }

        image_url = "https://example.com/document.pdf"

        # Act & Assert
        with pytest.raises(ErrInvalidImageExtension):
            await SearchLgtmImagesByImageFromUrlUsecase.execute(
                image_fetch_repository=mock_image_fetch_repo,
                search_repository=mock_search_repo,
                image_url=image_url,
            )

        mock_image_fetch_repo.fetch_image.assert_called_once_with(image_url)
        mock_search_repo.search_by_image.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("mime_type", "expected_extension"),
        [
            ("image/jpeg", ".jpg"),
            ("image/png", ".png"),
        ],
        ids=["jpeg", "png"],
    )
    async def test_execute_success_with_various_mime_types(
        self, mime_type: str, expected_extension: str
    ) -> None:
        """正常系: 各種MIMEタイプで正常に動作する."""
        # Arrange
        mock_image_fetch_repo = AsyncMock()
        mock_search_repo = AsyncMock()

        mock_image_fetch_repo.fetch_image.return_value = {
            "data": b"image data",
            "mime_type": mime_type,
        }

        mock_results: list[LgtmImageSearchResult] = [
            {
                "id": "1",
                "url": "https://example.com/image1.webp",
                "similarity_score": 0.90,
            }
        ]
        mock_search_repo.search_by_image.return_value = mock_results

        image_url = "https://example.com/image.jpg"

        # Act
        result = await SearchLgtmImagesByImageFromUrlUsecase.execute(
            image_fetch_repository=mock_image_fetch_repo,
            search_repository=mock_search_repo,
            image_url=image_url,
        )

        # Assert
        assert len(result) == 1
        assert result == mock_results
        call_args = mock_search_repo.search_by_image.call_args
        assert call_args.kwargs["image_extension"] == expected_extension
        assert call_args.kwargs["max_results"] == DEFAULT_SEARCH_MAX_RESULTS

    @pytest.mark.asyncio
    async def test_execute_success_with_empty_results(self) -> None:
        """正常系: 検索結果が0件の場合でも空のリストが返る."""
        # Arrange
        mock_image_fetch_repo = AsyncMock()
        mock_search_repo = AsyncMock()

        mock_image_fetch_repo.fetch_image.return_value = {
            "data": b"image data",
            "mime_type": "image/jpeg",
        }
        mock_search_repo.search_by_image.return_value = []

        image_url = "https://example.com/image.jpg"

        # Act
        result = await SearchLgtmImagesByImageFromUrlUsecase.execute(
            image_fetch_repository=mock_image_fetch_repo,
            search_repository=mock_search_repo,
            image_url=image_url,
        )

        # Assert
        assert len(result) == 0
        assert result == []
        mock_search_repo.search_by_image.assert_called_once()
