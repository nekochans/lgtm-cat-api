"""CreateLgtmImageFromUrlUseCaseのテスト."""

from unittest.mock import AsyncMock

import pytest

from domain.lgtm_image_errors import (
    ErrImageFetchFailed,
    ErrInvalidImageExtension,
    ErrInvalidUrl,
)
from usecase.create_lgtm_image_from_url_usecase import CreateLgtmImageFromUrlUseCase


class TestCreateLgtmImageFromUrlUseCase:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "image_url,image_data,mime_type,expected_extension",
        [
            (
                "https://example.com/image.png",
                b"\x89PNG\r\n\x1a\n" + b"\x00" * 100,
                "image/png",
                ".png",
            ),
            (
                "https://example.com/image.jpg",
                b"\xff\xd8\xff" + b"\x00" * 100,
                "image/jpeg",
                ".jpg",
            ),
        ],
    )
    async def test_execute_success(
        self,
        image_url: str,
        image_data: bytes,
        mime_type: str,
        expected_extension: str,
    ) -> None:
        """正常系: 画像の取得とアップロードに成功する."""
        # Arrange
        base_url = "lgtm-images.lgtmeow.com"

        mock_image_fetch_repo = AsyncMock()
        mock_image_fetch_repo.fetch_image = AsyncMock(
            return_value={"data": image_data, "mime_type": mime_type}
        )

        mock_storage_repo = AsyncMock()
        mock_storage_repo.upload = AsyncMock()

        # Act
        result = await CreateLgtmImageFromUrlUseCase.execute(
            image_fetch_repository=mock_image_fetch_repo,
            object_storage_repository=mock_storage_repo,
            base_url=base_url,
            image_url=image_url,
        )

        # Assert
        assert isinstance(result, dict)
        assert "url" in result
        assert result["url"].startswith(f"https://{base_url}/")
        assert result["url"].endswith(".webp")

        mock_image_fetch_repo.fetch_image.assert_called_once_with(image_url)
        mock_storage_repo.upload.assert_called_once()

        # uploadに渡されたパラメータを確認
        upload_call_args = mock_storage_repo.upload.call_args[0][0]
        assert upload_call_args["body"] == image_data
        assert upload_call_args["image_extension"] == expected_extension

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_image_fetch_fails(self) -> None:
        """異常系: 画像取得に失敗した場合、エラーを発生させる."""
        # Arrange
        image_url = "https://example.com/image.jpg"
        base_url = "lgtm-images.lgtmeow.com"

        mock_image_fetch_repo = AsyncMock()
        mock_image_fetch_repo.fetch_image = AsyncMock(
            side_effect=ErrImageFetchFailed("Failed to fetch")
        )

        mock_storage_repo = AsyncMock()

        # Act & Assert
        with pytest.raises(ErrImageFetchFailed):
            await CreateLgtmImageFromUrlUseCase.execute(
                image_fetch_repository=mock_image_fetch_repo,
                object_storage_repository=mock_storage_repo,
                base_url=base_url,
                image_url=image_url,
            )

        mock_storage_repo.upload.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_invalid_url(self) -> None:
        """異常系: 無効なURLの場合、エラーを発生させる."""
        # Arrange
        image_url = "http://localhost/image.jpg"
        base_url = "lgtm-images.lgtmeow.com"

        mock_image_fetch_repo = AsyncMock()
        mock_image_fetch_repo.fetch_image = AsyncMock(
            side_effect=ErrInvalidUrl("Invalid URL")
        )

        mock_storage_repo = AsyncMock()

        # Act & Assert
        with pytest.raises(ErrInvalidUrl):
            await CreateLgtmImageFromUrlUseCase.execute(
                image_fetch_repository=mock_image_fetch_repo,
                object_storage_repository=mock_storage_repo,
                base_url=base_url,
                image_url=image_url,
            )

        mock_storage_repo.upload.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_unsupported_format(self) -> None:
        """異常系: サポートされていない画像形式の場合、エラーを発生させる."""
        # Arrange
        image_url = "https://example.com/image.webp"
        base_url = "lgtm-images.lgtmeow.com"

        # WebPのマジックナンバー
        webp_data = b"RIFF" + b"\x00" * 4 + b"WEBP" + b"\x00" * 100

        mock_image_fetch_repo = AsyncMock()
        mock_image_fetch_repo.fetch_image = AsyncMock(
            return_value={"data": webp_data, "mime_type": "image/webp"}
        )

        mock_storage_repo = AsyncMock()

        # Act & Assert
        with pytest.raises(ErrInvalidImageExtension) as exc_info:
            await CreateLgtmImageFromUrlUseCase.execute(
                image_fetch_repository=mock_image_fetch_repo,
                object_storage_repository=mock_storage_repo,
                base_url=base_url,
                image_url=image_url,
            )

        assert "Unsupported MIME type" in str(exc_info.value)
        mock_storage_repo.upload.assert_not_called()
