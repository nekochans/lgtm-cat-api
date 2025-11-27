# 絶対厳守：編集前に必ずAI実装ルールを読む

import json
from typing import cast
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from domain.cat_image_validation_policy import CatImageValidationPolicy
from domain.lgtm_image_errors import ErrRekognitionFailed
from presentation.controller.cat_image_controller import CatImageController
from presentation.controller.cat_image_request import CatImageValidationFromS3Request


class TestCatImageControllerValidateFromS3:
    """CatImageController.validate_from_s3() のテスト.

    外部サービス（AI画像分析サービス、S3）に依存するため、UseCaseクラスをpatchしてテストする。
    """

    @pytest.mark.asyncio
    @patch("presentation.controller.cat_image_controller.ValidateCatImageFromS3UseCase")
    async def test_validate_from_s3_success_acceptable(
        self, mock_usecase_class: Mock
    ) -> None:
        """正常系: UseCaseがis_acceptable=Trueを返した場合、200を返す."""
        # Arrange
        mock_usecase_instance = MagicMock()
        mock_usecase_instance.execute = AsyncMock(return_value={"is_acceptable": True})
        mock_usecase_class.return_value = mock_usecase_instance

        request = CatImageValidationFromS3Request(
            bucketName="test-bucket",
            objectKey="images/cat.jpg",
        )
        mock_service = AsyncMock()
        mock_policy = cast(CatImageValidationPolicy, {})

        # Act
        response = await CatImageController.validate_from_s3(
            request, mock_service, mock_policy
        )

        # Assert
        assert response.status_code == 200
        response_data = json.loads(bytes(response.body))
        assert response_data["isAcceptableCatImage"] is True
        assert "notAcceptableReason" not in response_data

        # UseCaseが正しく呼び出されたことを確認
        mock_usecase_class.assert_called_once_with(mock_service, mock_policy)
        mock_usecase_instance.execute.assert_called_once_with(
            "test-bucket", "images/cat.jpg"
        )

    @pytest.mark.asyncio
    @patch("presentation.controller.cat_image_controller.ValidateCatImageFromS3UseCase")
    async def test_validate_from_s3_success_not_acceptable_not_cat(
        self, mock_usecase_class: Mock
    ) -> None:
        """正常系: 猫が検出されなかった場合、200とreasonを返す."""
        # Arrange
        mock_usecase_instance = MagicMock()
        mock_usecase_instance.execute = AsyncMock(
            return_value={"is_acceptable": False, "reason": "not cat image"}
        )
        mock_usecase_class.return_value = mock_usecase_instance

        request = CatImageValidationFromS3Request(
            bucketName="test-bucket",
            objectKey="images/dog.jpg",
        )
        mock_service = AsyncMock()
        mock_policy = cast(CatImageValidationPolicy, {})

        # Act
        response = await CatImageController.validate_from_s3(
            request, mock_service, mock_policy
        )

        # Assert
        assert response.status_code == 200
        response_data = json.loads(bytes(response.body))
        assert response_data["isAcceptableCatImage"] is False
        assert response_data["notAcceptableReason"] == "not cat image"

    @pytest.mark.asyncio
    @patch("presentation.controller.cat_image_controller.ValidateCatImageFromS3UseCase")
    async def test_validate_from_s3_success_not_acceptable_person_face(
        self, mock_usecase_class: Mock
    ) -> None:
        """正常系: 人の顔が検出された場合、200とreasonを返す."""
        # Arrange
        mock_usecase_instance = MagicMock()
        mock_usecase_instance.execute = AsyncMock(
            return_value={"is_acceptable": False, "reason": "person face in the image"}
        )
        mock_usecase_class.return_value = mock_usecase_instance

        request = CatImageValidationFromS3Request(
            bucketName="test-bucket",
            objectKey="images/person.jpg",
        )
        mock_service = AsyncMock()
        mock_policy = cast(CatImageValidationPolicy, {})

        # Act
        response = await CatImageController.validate_from_s3(
            request, mock_service, mock_policy
        )

        # Assert
        assert response.status_code == 200
        response_data = json.loads(bytes(response.body))
        assert response_data["isAcceptableCatImage"] is False
        assert response_data["notAcceptableReason"] == "person face in the image"

    @pytest.mark.asyncio
    @patch("presentation.controller.cat_image_controller.ValidateCatImageFromS3UseCase")
    async def test_validate_from_s3_success_not_acceptable_moderation(
        self, mock_usecase_class: Mock
    ) -> None:
        """正常系: 不適切コンテンツが検出された場合、200とreasonを返す."""
        # Arrange
        mock_usecase_instance = MagicMock()
        mock_usecase_instance.execute = AsyncMock(
            return_value={"is_acceptable": False, "reason": "not moderation image"}
        )
        mock_usecase_class.return_value = mock_usecase_instance

        request = CatImageValidationFromS3Request(
            bucketName="test-bucket",
            objectKey="images/inappropriate.jpg",
        )
        mock_service = AsyncMock()
        mock_policy = cast(CatImageValidationPolicy, {})

        # Act
        response = await CatImageController.validate_from_s3(
            request, mock_service, mock_policy
        )

        # Assert
        assert response.status_code == 200
        response_data = json.loads(bytes(response.body))
        assert response_data["isAcceptableCatImage"] is False
        assert response_data["notAcceptableReason"] == "not moderation image"

    @pytest.mark.asyncio
    @patch("presentation.controller.cat_image_controller.ValidateCatImageFromS3UseCase")
    async def test_validate_from_s3_rekognition_failed_error(
        self, mock_usecase_class: Mock
    ) -> None:
        """例外系: ErrRekognitionFailedが発生した場合、500を返す."""
        # Arrange
        mock_usecase_instance = MagicMock()
        mock_usecase_instance.execute = AsyncMock(
            side_effect=ErrRekognitionFailed("Rekognition API error")
        )
        mock_usecase_class.return_value = mock_usecase_instance

        request = CatImageValidationFromS3Request(
            bucketName="test-bucket",
            objectKey="images/cat.jpg",
        )
        mock_service = AsyncMock()
        mock_policy = cast(CatImageValidationPolicy, {})

        # Act
        response = await CatImageController.validate_from_s3(
            request, mock_service, mock_policy
        )

        # Assert
        assert response.status_code == 500
        response_data = json.loads(bytes(response.body))
        assert response_data["error"] == "Internal server error"

    @pytest.mark.asyncio
    @patch("presentation.controller.cat_image_controller.ValidateCatImageFromS3UseCase")
    async def test_validate_from_s3_unexpected_error(
        self, mock_usecase_class: Mock
    ) -> None:
        """例外系: 予期しない例外が発生した場合、500を返す."""
        # Arrange
        mock_usecase_instance = MagicMock()
        mock_usecase_instance.execute = AsyncMock(
            side_effect=Exception("Unexpected error")
        )
        mock_usecase_class.return_value = mock_usecase_instance

        request = CatImageValidationFromS3Request(
            bucketName="test-bucket",
            objectKey="images/cat.jpg",
        )
        mock_service = AsyncMock()
        mock_policy = cast(CatImageValidationPolicy, {})

        # Act
        response = await CatImageController.validate_from_s3(
            request, mock_service, mock_policy
        )

        # Assert
        assert response.status_code == 500
        response_data = json.loads(bytes(response.body))
        assert response_data["error"] == "Internal server error"
