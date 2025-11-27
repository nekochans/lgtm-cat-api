# 絶対厳守：編集前に必ずAI実装ルールを読む

import base64
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from domain.lgtm_image_errors import (
    ErrImageFetchFailed,
    ErrInvalidImageExtension,
    ErrInvalidUrl,
    ErrUrlNotAccessible,
)
from presentation.controller.lgtm_image_controller import LgtmImageController
from presentation.controller.lgtm_image_request import (
    LgtmImageCreateFromUrlRequest,
    LgtmImageCreateRequest,
)


class TestLgtmImageControllerCreate:
    """LgtmImageController.create() のテスト.

    外部サービス（オブジェクトストレージ）に依存するため、
    UseCaseクラスをpatchしてテストする。
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "extension",
        [".png", ".jpg", ".jpeg"],
        ids=["png", "jpg", "jpeg"],
    )
    @patch("presentation.controller.lgtm_image_controller.CreateLgtmImageUsecase")
    async def test_create_success_with_valid_extensions(
        self, mock_usecase_class: Mock, extension: str
    ) -> None:
        """正常系: 有効な拡張子で正しく画像を作成できる."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(
            return_value={
                "url": "https://storage.example.com/2025/01/test-uuid-789.webp"
            }
        )

        object_storage_repository = Mock()
        base_url = "storage.example.com"

        test_image_data = b"test image"
        encoded_image = base64.b64encode(test_image_data).decode("utf-8")

        request_body = LgtmImageCreateRequest(
            image=encoded_image, imageExtension=extension
        )

        # Act
        result = await LgtmImageController.create(
            object_storage_repository=object_storage_repository,
            base_url=base_url,
            request_body=request_body,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 202

        content = json.loads(bytes(result.body))
        assert "imageUrl" in content
        assert (
            content["imageUrl"]
            == "https://storage.example.com/2025/01/test-uuid-789.webp"
        )

        # UseCaseが正しく呼ばれたことを確認
        mock_usecase_class.execute.assert_called_once()

    def test_create_raises_error_with_invalid_extension(self) -> None:
        """異常系: 無効な拡張子でPydantic ValidationErrorが発生する."""
        # Arrange
        test_image_data = b"test gif image"
        encoded_image = base64.b64encode(test_image_data).decode("utf-8")

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            LgtmImageCreateRequest(image=encoded_image, imageExtension=".gif")

        # バリデーションエラーの詳細を確認
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("imageExtension",)
        assert "Invalid image extension" in str(errors[0]["msg"])

    @pytest.mark.asyncio
    @patch("presentation.controller.lgtm_image_controller.CreateLgtmImageUsecase")
    async def test_create_raises_error_with_object_storage_failure(
        self, mock_usecase_class: Mock
    ) -> None:
        """異常系: アップロード失敗で500エラーを返す."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(
            side_effect=Exception("object storage upload failed")
        )

        object_storage_repository = Mock()
        base_url = "example.com"

        test_image_data = b"test image"
        encoded_image = base64.b64encode(test_image_data).decode("utf-8")

        request_body = LgtmImageCreateRequest(
            image=encoded_image, imageExtension=".png"
        )

        # Act
        result = await LgtmImageController.create(
            object_storage_repository=object_storage_repository,
            base_url=base_url,
            request_body=request_body,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500

        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "Internal server error" in content["error"]


class TestLgtmImageControllerCreateFromUrl:
    """LgtmImageController.create_from_url() のテスト.

    外部サービス（画像取得、オブジェクトストレージ）に依存するため、
    UseCaseクラスをpatchしてテストする。
    """

    @pytest.mark.asyncio
    @patch(
        "presentation.controller.lgtm_image_controller.CreateLgtmImageFromUrlUseCase"
    )
    async def test_create_from_url_success(self, mock_usecase_class: Mock) -> None:
        """正常系: 許可されたURLから画像を取得してアップロードに成功する."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(
            return_value={
                "url": "https://lgtm-images.lgtmeow.com/2025/01/test-uuid-url.webp"
            }
        )

        image_url = "https://example.com/image.png"
        base_url = "lgtm-images.lgtmeow.com"

        mock_image_fetch_repo = AsyncMock()
        mock_storage_repo = AsyncMock()

        request_body = LgtmImageCreateFromUrlRequest(imageUrl=image_url)

        # Act
        result = await LgtmImageController.create_from_url(
            image_fetch_repository=mock_image_fetch_repo,
            object_storage_repository=mock_storage_repo,
            base_url=base_url,
            request_body=request_body,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 202

        content = json.loads(bytes(result.body))
        assert "imageUrl" in content
        assert "lgtm-images.lgtmeow.com" in content["imageUrl"]
        assert content["imageUrl"].endswith(".webp")

        mock_usecase_class.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "presentation.controller.lgtm_image_controller.CreateLgtmImageFromUrlUseCase"
    )
    async def test_create_from_url_invalid_url_error(
        self, mock_usecase_class: Mock
    ) -> None:
        """異常系: 無効なURLの場合、400エラーを返す."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(side_effect=ErrInvalidUrl("Invalid URL"))

        image_url = "https://localhost/image.png"
        base_url = "lgtm-images.lgtmeow.com"

        mock_image_fetch_repo = AsyncMock()
        mock_storage_repo = AsyncMock()

        request_body = LgtmImageCreateFromUrlRequest(imageUrl=image_url)

        # Act
        result = await LgtmImageController.create_from_url(
            image_fetch_repository=mock_image_fetch_repo,
            object_storage_repository=mock_storage_repo,
            base_url=base_url,
            request_body=request_body,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 400

        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "Invalid URL provided" in content["error"]

    @pytest.mark.asyncio
    @patch(
        "presentation.controller.lgtm_image_controller.CreateLgtmImageFromUrlUseCase"
    )
    async def test_create_from_url_not_accessible_error(
        self, mock_usecase_class: Mock
    ) -> None:
        """異常系: URLにアクセスできない場合、400エラーを返す."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(
            side_effect=ErrUrlNotAccessible("URL not found")
        )

        image_url = "https://example.com/not-found.png"
        base_url = "lgtm-images.lgtmeow.com"

        mock_image_fetch_repo = AsyncMock()
        mock_storage_repo = AsyncMock()

        request_body = LgtmImageCreateFromUrlRequest(imageUrl=image_url)

        # Act
        result = await LgtmImageController.create_from_url(
            image_fetch_repository=mock_image_fetch_repo,
            object_storage_repository=mock_storage_repo,
            base_url=base_url,
            request_body=request_body,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 400

        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "URL not accessible" in content["error"]

    @pytest.mark.asyncio
    @patch(
        "presentation.controller.lgtm_image_controller.CreateLgtmImageFromUrlUseCase"
    )
    async def test_create_from_url_fetch_failed_error(
        self, mock_usecase_class: Mock
    ) -> None:
        """異常系: 画像取得失敗の場合、422エラーを返す."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(
            side_effect=ErrImageFetchFailed("Failed to fetch")
        )

        image_url = "https://example.com/image.png"
        base_url = "lgtm-images.lgtmeow.com"

        mock_image_fetch_repo = AsyncMock()
        mock_storage_repo = AsyncMock()

        request_body = LgtmImageCreateFromUrlRequest(imageUrl=image_url)

        # Act
        result = await LgtmImageController.create_from_url(
            image_fetch_repository=mock_image_fetch_repo,
            object_storage_repository=mock_storage_repo,
            base_url=base_url,
            request_body=request_body,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 422

        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "Failed to fetch image from URL" in content["error"]

    @pytest.mark.asyncio
    @patch(
        "presentation.controller.lgtm_image_controller.CreateLgtmImageFromUrlUseCase"
    )
    async def test_create_from_url_invalid_extension_error(
        self, mock_usecase_class: Mock
    ) -> None:
        """異常系: サポートされていない画像形式の場合、422エラーを返す."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(
            side_effect=ErrInvalidImageExtension("Unsupported MIME type")
        )

        image_url = "https://example.com/image.gif"
        base_url = "lgtm-images.lgtmeow.com"

        mock_image_fetch_repo = AsyncMock()
        mock_storage_repo = AsyncMock()

        request_body = LgtmImageCreateFromUrlRequest(imageUrl=image_url)

        # Act
        result = await LgtmImageController.create_from_url(
            image_fetch_repository=mock_image_fetch_repo,
            object_storage_repository=mock_storage_repo,
            base_url=base_url,
            request_body=request_body,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 422

        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "Invalid image extension or unsupported format" in content["error"]

    @pytest.mark.asyncio
    @patch(
        "presentation.controller.lgtm_image_controller.CreateLgtmImageFromUrlUseCase"
    )
    async def test_create_from_url_general_exception_error(
        self, mock_usecase_class: Mock
    ) -> None:
        """異常系: 予期しないエラーの場合、500エラーを返す."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        image_url = "https://example.com/image.png"
        base_url = "lgtm-images.lgtmeow.com"

        mock_image_fetch_repo = AsyncMock()
        mock_storage_repo = AsyncMock()

        request_body = LgtmImageCreateFromUrlRequest(imageUrl=image_url)

        # Act
        result = await LgtmImageController.create_from_url(
            image_fetch_repository=mock_image_fetch_repo,
            object_storage_repository=mock_storage_repo,
            base_url=base_url,
            request_body=request_body,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500

        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "Internal server error" in content["error"]
