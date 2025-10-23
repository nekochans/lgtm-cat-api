# 絶対厳守：編集前に必ずAI実装ルールを読む

import base64
from unittest.mock import AsyncMock, Mock, patch

import pytest

from domain.create_lgtm_image import UploadObjectStorageDto
from usecase.create_lgtm_image_usecase import CreateLgtmImageUsecase


@pytest.mark.asyncio
async def test_create_lgtm_image_usecase_success() -> None:
    """CreateLgtmImageUsecaseが正常に実行されることを確認."""
    # Arrange
    object_storage_repository = Mock()
    object_storage_repository.upload = AsyncMock()

    cdn_domain = "lgtm-images.lgtmeow.com"

    # base64エンコードされたテスト画像データ
    test_image_data = b"test image binary"
    encoded_image = base64.b64encode(test_image_data).decode("utf-8")

    # Act
    with patch(
        "usecase.create_lgtm_image_usecase.generate_lgtm_image_name",
        return_value="test-uuid-123",
    ):
        result = await CreateLgtmImageUsecase.execute(
            object_storage_repository=object_storage_repository,
            base_url=cdn_domain,
            image=encoded_image,
            image_extension=".png",
        )

    # Assert
    assert "url" in result
    assert "lgtm-images.lgtmeow.com" in result["url"]
    assert "test-uuid-123" in result["url"]
    assert result["url"].endswith(".webp")

    # リポジトリのuploadが1回呼ばれたことを確認
    object_storage_repository.upload.assert_called_once()

    # uploadに渡されたパラメータを確認
    call_args = object_storage_repository.upload.call_args
    upload_param: UploadObjectStorageDto = call_args[0][0]
    assert upload_param["body"] == test_image_data
    assert upload_param["image_extension"] == ".png"
    assert "test-uuid-123.png" in upload_param["key"]


@pytest.mark.asyncio
async def test_create_lgtm_image_usecase_decodes_base64() -> None:
    """base64データが正しくデコードされることを確認."""
    # Arrange
    object_storage_repository = Mock()
    object_storage_repository.upload = AsyncMock()

    base_url = "lgtm-images.lgtmeow.com"

    # パディングなしのbase64（Python はパディングを補完してくれる）
    test_data = "test"
    encoded = base64.b64encode(test_data.encode()).decode("utf-8")

    # Act
    with patch(
        "usecase.create_lgtm_image_usecase.generate_lgtm_image_name",
        return_value="test-uuid-123",
    ):
        result = await CreateLgtmImageUsecase.execute(
            object_storage_repository=object_storage_repository,
            base_url=base_url,
            image=encoded,
            image_extension=".png",
        )

    # Assert
    assert "url" in result
    object_storage_repository.upload.assert_called_once()

    # デコードされたデータが正しく渡されていることを確認
    call_args = object_storage_repository.upload.call_args
    upload_param: UploadObjectStorageDto = call_args[0][0]
    assert upload_param["body"] == test_data.encode()
