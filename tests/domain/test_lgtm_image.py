# 絶対厳守：編集前に必ずAI実装ルールを読む

from domain.lgtm_image import LgtmImage
from domain.lgtm_image import DEFAULT_RANDOM_IMAGES_LIMIT


def test_default_random_images_limit_value() -> None:
    """DEFAULT_RANDOM_IMAGES_LIMITの値が正しいことを確認."""
    # Act & Assert
    assert DEFAULT_RANDOM_IMAGES_LIMIT == 9


def test_default_random_images_limit_type() -> None:
    """DEFAULT_RANDOM_IMAGES_LIMITの型がintであることを確認."""
    # Act & Assert
    assert isinstance(DEFAULT_RANDOM_IMAGES_LIMIT, int)


def test_lgtm_image_creation() -> None:
    """LgtmImageエンティティの作成テスト."""
    # Arrange & Act
    image = LgtmImage(
        id="test-id-123",
        url="https://lgtm-images.lgtmeow.com/test.webp",
    )

    # Assert
    assert image["id"] == "test-id-123"
    assert image["url"] == "https://lgtm-images.lgtmeow.com/test.webp"


def test_lgtm_image_equality() -> None:
    """LgtmImageエンティティの等価性テスト."""
    # Arrange
    image1 = LgtmImage(
        id="test-id",
        url="https://lgtm-images.lgtmeow.com/test.webp",
    )
    image2 = LgtmImage(
        id="test-id",
        url="https://lgtm-images.lgtmeow.com/test.webp",
    )
    image3 = LgtmImage(
        id="different-id",
        url="https://lgtm-images.lgtmeow.com/test.webp",
    )

    # Act & Assert
    assert image1 == image2
    assert image1 != image3
