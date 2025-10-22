# 絶対厳守：編集前に必ずAI実装ルールを読む

from datetime import datetime, timezone

import pytest

from src.domain.create_lgtm_image import (
    UploadS3Param,
    UploadedLgtmImage,
    build_s3_prefix,
    can_convert_image_extension,
    create_upload_s3_param,
    create_uploaded_lgtm_image,
)


@pytest.mark.parametrize("ext", [".png", ".jpg", ".jpeg"])
def test_can_convert_image_extension_valid(ext: str) -> None:
    """有効な拡張子が変換可能と判定されることを確認."""
    assert can_convert_image_extension(ext) is True


@pytest.mark.parametrize("ext", [".gif", ".webp", "png", ""])
def test_can_convert_image_extension_invalid(ext: str) -> None:
    """無効な拡張子が変換不可と判定されることを確認."""
    assert can_convert_image_extension(ext) is False


def test_build_s3_prefix() -> None:
    """S3プレフィックスが正しく生成されることを確認（東京時間）."""
    # Arrange
    # UTC時間: 2024-01-15 05:30:00 (JST: 2024-01-15 14:30:00)
    dt_utc = datetime(2024, 1, 15, 5, 30, 0, tzinfo=timezone.utc)

    # Act
    result = build_s3_prefix(dt_utc)

    # Assert
    # 東京時間（UTC+9）で14時になる
    assert result == "2024/01/15/14/"


def test_build_s3_prefix_midnight() -> None:
    """深夜の時刻でS3プレフィックスが正しく生成されることを確認."""
    # Arrange
    # UTC時間: 2024-01-14 15:00:00 (JST: 2024-01-15 00:00:00)
    dt_utc = datetime(2024, 1, 14, 15, 0, 0, tzinfo=timezone.utc)

    # Act
    result = build_s3_prefix(dt_utc)

    # Assert
    # 東京時間（UTC+9）で日付が変わる
    assert result == "2024/01/15/00/"


def test_create_upload_s3_param() -> None:
    """S3アップロードパラメータが正しく生成されることを確認."""
    # Arrange
    body = b"test image data"
    prefix = "2024/01/15/14/"
    image_name = "test-uuid-123"
    image_extension = ".png"

    # Act
    result = create_upload_s3_param(body, prefix, image_name, image_extension)

    # Assert
    assert result["body"] == body
    assert result["image_extension"] == image_extension
    assert result["key"] == "2024/01/15/14/test-uuid-123.png"


def test_create_uploaded_lgtm_image() -> None:
    """アップロード済みLGTM画像エンティティが正しく生成されることを確認."""
    # Arrange
    domain = "lgtm-images.lgtmeow.com"
    prefix = "2024/01/15/14/"
    image_name = "test-uuid-123"

    # Act
    result = create_uploaded_lgtm_image(domain, prefix, image_name)

    # Assert
    assert (
        result["url"]
        == "https://lgtm-images.lgtmeow.com/2024/01/15/14/test-uuid-123.webp"
    )


def test_uploaded_lgtm_image_type() -> None:
    """UploadedLgtmImageが正しい型であることを確認."""
    # Arrange & Act
    image: UploadedLgtmImage = UploadedLgtmImage(
        url="https://lgtm-images.lgtmeow.com/test.webp"
    )

    # Assert
    assert image["url"] == "https://lgtm-images.lgtmeow.com/test.webp"


def test_upload_s3_param_type() -> None:
    """UploadS3Paramが正しい型であることを確認."""
    # Arrange & Act
    param: UploadS3Param = UploadS3Param(
        body=b"test data", image_extension=".png", key="test/path/image.png"
    )

    # Assert
    assert param["body"] == b"test data"
    assert param["image_extension"] == ".png"
    assert param["key"] == "test/path/image.png"
