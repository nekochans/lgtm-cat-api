# 絶対厳守：編集前に必ずAI実装ルールを読む

import json
from typing import cast
from unittest.mock import AsyncMock, Mock, patch

import pytest

from domain.cat_image_validation_policy import CatImageValidationPolicy
from domain.lgtm_image_errors import (
    ErrImageFetchFailed,
    ErrInvalidImageExtension,
    ErrInvalidUrl,
    ErrRekognitionFailed,
    ErrUrlNotAccessible,
)
from presentation.controller.lgtm_image_controller import LgtmImageController
from presentation.controller.lgtm_image_request import CatImageValidationRequest


class TestLgtmImageControllerValidateCatImage:
    """LgtmImageController.validate_cat_image() のテスト.

    外部サービス（AI画像分析サービス）に依存するため、UseCaseクラスをpatchしてテストする。
    """

    @pytest.mark.asyncio
    @patch("presentation.controller.lgtm_image_controller.ValidateCatImageUseCase")
    async def test_validate_cat_image_success_acceptable(
        self, mock_usecase_class: Mock
    ) -> None:
        """正常系: UseCaseがis_acceptable=Trueを返した場合、200を返す."""
        # Arrange
        mock_usecase_instance = AsyncMock()
        mock_usecase_instance.execute = AsyncMock(return_value={"is_acceptable": True})
        mock_usecase_class.return_value = mock_usecase_instance

        request = CatImageValidationRequest(imageUrl="https://example.com/cat.jpg")
        mock_service = AsyncMock()
        mock_repo = AsyncMock()
        mock_policy = cast(CatImageValidationPolicy, {})

        # Act
        response = await LgtmImageController.validate_cat_image(
            request, mock_service, mock_repo, mock_policy
        )

        # Assert
        assert response.status_code == 200
        response_data = json.loads(bytes(response.body))
        assert response_data["isAcceptableCatImage"] is True
        assert "notAcceptableReason" not in response_data

    @pytest.mark.asyncio
    @patch("presentation.controller.lgtm_image_controller.ValidateCatImageUseCase")
    async def test_validate_cat_image_success_not_acceptable(
        self, mock_usecase_class: Mock
    ) -> None:
        """正常系: UseCaseがis_acceptable=Falseを返した場合、200とreasonを返す."""
        # Arrange
        mock_usecase_instance = AsyncMock()
        mock_usecase_instance.execute = AsyncMock(
            return_value={"is_acceptable": False, "reason": "test reason"}
        )
        mock_usecase_class.return_value = mock_usecase_instance

        request = CatImageValidationRequest(imageUrl="https://example.com/cat.jpg")
        mock_service = AsyncMock()
        mock_repo = AsyncMock()
        mock_policy = cast(CatImageValidationPolicy, {})

        # Act
        response = await LgtmImageController.validate_cat_image(
            request, mock_service, mock_repo, mock_policy
        )

        # Assert
        assert response.status_code == 200
        response_data = json.loads(bytes(response.body))
        assert response_data["isAcceptableCatImage"] is False
        assert response_data["notAcceptableReason"] == "test reason"

    @pytest.mark.asyncio
    @patch("presentation.controller.lgtm_image_controller.ValidateCatImageUseCase")
    async def test_validate_cat_image_invalid_url_error(
        self, mock_usecase_class: Mock
    ) -> None:
        """例外系: ErrInvalidUrlが発生した場合、400を返す."""
        # Arrange
        mock_usecase_instance = AsyncMock()
        mock_usecase_instance.execute = AsyncMock(
            side_effect=ErrInvalidUrl("Invalid URL")
        )
        mock_usecase_class.return_value = mock_usecase_instance

        request = CatImageValidationRequest(imageUrl="https://example.com/cat.jpg")
        mock_service = AsyncMock()
        mock_repo = AsyncMock()
        mock_policy = cast(CatImageValidationPolicy, {})

        # Act
        response = await LgtmImageController.validate_cat_image(
            request, mock_service, mock_repo, mock_policy
        )

        # Assert
        assert response.status_code == 400
        response_data = json.loads(bytes(response.body))
        assert response_data["error"] == "Invalid URL provided"

    @pytest.mark.asyncio
    @patch("presentation.controller.lgtm_image_controller.ValidateCatImageUseCase")
    async def test_validate_cat_image_url_not_accessible_error(
        self, mock_usecase_class: Mock
    ) -> None:
        """例外系: ErrUrlNotAccessibleが発生した場合、400を返す."""
        # Arrange
        mock_usecase_instance = AsyncMock()
        mock_usecase_instance.execute = AsyncMock(
            side_effect=ErrUrlNotAccessible("URL not accessible")
        )
        mock_usecase_class.return_value = mock_usecase_instance

        request = CatImageValidationRequest(imageUrl="https://example.com/cat.jpg")
        mock_service = AsyncMock()
        mock_repo = AsyncMock()
        mock_policy = cast(CatImageValidationPolicy, {})

        # Act
        response = await LgtmImageController.validate_cat_image(
            request, mock_service, mock_repo, mock_policy
        )

        # Assert
        assert response.status_code == 400
        response_data = json.loads(bytes(response.body))
        assert response_data["error"] == "URL not accessible"

    @pytest.mark.asyncio
    @patch("presentation.controller.lgtm_image_controller.ValidateCatImageUseCase")
    async def test_validate_cat_image_fetch_failed_error(
        self, mock_usecase_class: Mock
    ) -> None:
        """例外系: ErrImageFetchFailedが発生した場合、422を返す."""
        # Arrange
        mock_usecase_instance = AsyncMock()
        mock_usecase_instance.execute = AsyncMock(
            side_effect=ErrImageFetchFailed("Fetch failed")
        )
        mock_usecase_class.return_value = mock_usecase_instance

        request = CatImageValidationRequest(imageUrl="https://example.com/cat.jpg")
        mock_service = AsyncMock()
        mock_repo = AsyncMock()
        mock_policy = cast(CatImageValidationPolicy, {})

        # Act
        response = await LgtmImageController.validate_cat_image(
            request, mock_service, mock_repo, mock_policy
        )

        # Assert
        assert response.status_code == 422
        response_data = json.loads(bytes(response.body))
        assert response_data["error"] == "Failed to fetch image from URL"

    @pytest.mark.asyncio
    @patch("presentation.controller.lgtm_image_controller.ValidateCatImageUseCase")
    async def test_validate_cat_image_invalid_extension_error(
        self, mock_usecase_class: Mock
    ) -> None:
        """例外系: ErrInvalidImageExtensionが発生した場合、422を返す."""
        # Arrange
        mock_usecase_instance = AsyncMock()
        mock_usecase_instance.execute = AsyncMock(
            side_effect=ErrInvalidImageExtension("Invalid extension")
        )
        mock_usecase_class.return_value = mock_usecase_instance

        request = CatImageValidationRequest(imageUrl="https://example.com/cat.jpg")
        mock_service = AsyncMock()
        mock_repo = AsyncMock()
        mock_policy = cast(CatImageValidationPolicy, {})

        # Act
        response = await LgtmImageController.validate_cat_image(
            request, mock_service, mock_repo, mock_policy
        )

        # Assert
        assert response.status_code == 422
        response_data = json.loads(bytes(response.body))
        assert response_data["error"] == "Invalid image extension or unsupported format"

    @pytest.mark.asyncio
    @patch("presentation.controller.lgtm_image_controller.ValidateCatImageUseCase")
    async def test_validate_cat_image_rekognition_failed_error(
        self, mock_usecase_class: Mock
    ) -> None:
        """例外系: ErrRekognitionFailedが発生した場合、500を返す."""
        # Arrange
        mock_usecase_instance = AsyncMock()
        mock_usecase_instance.execute = AsyncMock(
            side_effect=ErrRekognitionFailed("Rekognition API error")
        )
        mock_usecase_class.return_value = mock_usecase_instance

        request = CatImageValidationRequest(imageUrl="https://example.com/cat.jpg")
        mock_service = AsyncMock()
        mock_repo = AsyncMock()
        mock_policy = cast(CatImageValidationPolicy, {})

        # Act
        response = await LgtmImageController.validate_cat_image(
            request, mock_service, mock_repo, mock_policy
        )

        # Assert
        assert response.status_code == 500
        response_data = json.loads(bytes(response.body))
        assert response_data["error"] == "Internal server error"

    @pytest.mark.asyncio
    @patch("presentation.controller.lgtm_image_controller.ValidateCatImageUseCase")
    async def test_validate_cat_image_unexpected_error(
        self, mock_usecase_class: Mock
    ) -> None:
        """例外系: 予期しない例外が発生した場合、500を返す."""
        # Arrange
        mock_usecase_instance = AsyncMock()
        mock_usecase_instance.execute = AsyncMock(
            side_effect=Exception("Unexpected error")
        )
        mock_usecase_class.return_value = mock_usecase_instance

        request = CatImageValidationRequest(imageUrl="https://example.com/cat.jpg")
        mock_service = AsyncMock()
        mock_repo = AsyncMock()
        mock_policy = cast(CatImageValidationPolicy, {})

        # Act
        response = await LgtmImageController.validate_cat_image(
            request, mock_service, mock_repo, mock_policy
        )

        # Assert
        assert response.status_code == 500
        response_data = json.loads(bytes(response.body))
        assert response_data["error"] == "Internal server error"
