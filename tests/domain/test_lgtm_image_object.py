# 絶対厳守：編集前に必ずAI実装ルールを読む

from domain.lgtm_image import LgtmImageId
from domain.lgtm_image_object import LgtmImageObject, create_lgtm_image


def test_lgtm_image_object_creation() -> None:
    """LgtmImageObjectエンティティの作成テスト."""
    # Arrange & Act
    image_obj = LgtmImageObject(
        id=LgtmImageId(1),
        path="2021/03/16/23",
        filename="5947f291-a46e-453c-a230-0d756d7174cb.webp",
    )

    # Assert
    assert image_obj["id"] == LgtmImageId(1)
    assert image_obj["path"] == "2021/03/16/23"
    assert image_obj["filename"] == "5947f291-a46e-453c-a230-0d756d7174cb.webp"


def test_lgtm_image_object_equality() -> None:
    """LgtmImageObjectエンティティの等価性テスト."""
    # Arrange
    image_obj1 = LgtmImageObject(
        id=LgtmImageId(1),
        path="2021/03/16/23",
        filename="test.webp",
    )
    image_obj2 = LgtmImageObject(
        id=LgtmImageId(1),
        path="2021/03/16/23",
        filename="test.webp",
    )
    image_obj3 = LgtmImageObject(
        id=LgtmImageId(2),
        path="2021/03/16/23",
        filename="test.webp",
    )

    # Act & Assert
    assert image_obj1 == image_obj2
    assert image_obj1 != image_obj3


def test_to_lgtm_image_conversion() -> None:
    """LgtmImageObjectからLgtmImageへの変換テスト."""
    # Arrange
    image_obj = LgtmImageObject(
        id=LgtmImageId(1),
        path="2021/03/16/23",
        filename="5947f291-a46e-453c-a230-0d756d7174cb.webp",
    )
    base_url = "lgtm-images.lgtmeow.com"

    # Act
    lgtm_image = create_lgtm_image(image_obj, base_url)

    # Assert
    assert lgtm_image["id"] == "1"
    assert (
        lgtm_image["url"]
        == "https://lgtm-images.lgtmeow.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp"
    )


def test_to_lgtm_image_url_format() -> None:
    """LgtmImageへの変換時のURL形式テスト."""
    # Arrange
    image_obj = LgtmImageObject(
        id=LgtmImageId(123),
        path="2024/12/31/10",
        filename="test-image.webp",
    )
    base_url = "lgtm-images.lgtmeow.com"

    # Act
    lgtm_image = create_lgtm_image(image_obj, base_url)

    # Assert
    assert (
        lgtm_image["url"]
        == "https://lgtm-images.lgtmeow.com/2024/12/31/10/test-image.webp"
    )
