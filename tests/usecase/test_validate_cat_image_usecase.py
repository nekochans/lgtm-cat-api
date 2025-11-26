# 絶対厳守：編集前に必ずAI実装ルールを読む
"""ValidateCatImageUseCaseのテスト"""

from unittest.mock import AsyncMock

import pytest

from domain.cat_image_validation_policy import (
    CatImageValidationPolicy,
    DEFAULT_VALIDATION_POLICY,
)
from usecase.validate_cat_image_usecase import ValidateCatImageUseCase
from domain.lgtm_image_errors import ErrImageFetchFailed
from domain.image_analysis_interface import (
    FaceDetection,
    LabelDetection,
    ModerationLabelDetection,
)


@pytest.mark.asyncio
async def test_execute_acceptable_cat_image() -> None:
    """受け入れ可能な猫画像のテスト"""
    mock_image_analysis_service = AsyncMock()
    mock_image_analysis_service.detect_moderation_labels = AsyncMock(return_value=[])
    mock_image_analysis_service.detect_faces = AsyncMock(return_value=[])
    mock_image_analysis_service.detect_labels = AsyncMock(
        return_value=[LabelDetection(name="Cat", confidence=95.0)]
    )

    mock_image_fetch_repo = AsyncMock()
    mock_image_fetch_repo.fetch_image = AsyncMock(
        return_value={"data": b"fake_image_data", "mime_type": "image/jpeg"}
    )

    usecase = ValidateCatImageUseCase(
        mock_image_analysis_service, mock_image_fetch_repo, DEFAULT_VALIDATION_POLICY
    )
    result = await usecase.execute("https://example.com/cat.jpg")

    assert result["is_acceptable"] is True
    assert "reason" not in result


@pytest.mark.asyncio
async def test_execute_not_cat_image() -> None:
    """猫が写っていない画像のテスト"""
    mock_image_analysis_service = AsyncMock()
    mock_image_analysis_service.detect_moderation_labels = AsyncMock(return_value=[])
    mock_image_analysis_service.detect_faces = AsyncMock(return_value=[])
    mock_image_analysis_service.detect_labels = AsyncMock(
        return_value=[LabelDetection(name="Dog", confidence=95.0)]
    )

    mock_image_fetch_repo = AsyncMock()
    mock_image_fetch_repo.fetch_image = AsyncMock(
        return_value={"data": b"fake_image_data", "mime_type": "image/jpeg"}
    )

    usecase = ValidateCatImageUseCase(
        mock_image_analysis_service, mock_image_fetch_repo, DEFAULT_VALIDATION_POLICY
    )
    result = await usecase.execute("https://example.com/dog.jpg")

    assert result["is_acceptable"] is False
    assert result["reason"] == "not cat image"


@pytest.mark.asyncio
async def test_execute_person_face_detected() -> None:
    """人の顔が検出された画像のテスト"""
    mock_image_analysis_service = AsyncMock()
    mock_image_analysis_service.detect_moderation_labels = AsyncMock(return_value=[])
    # 信頼度97.0の顔を検出（96.0超でNG）
    mock_image_analysis_service.detect_faces = AsyncMock(
        return_value=[FaceDetection(confidence=97.0)]
    )
    mock_image_analysis_service.detect_labels = AsyncMock(
        return_value=[LabelDetection(name="Cat", confidence=95.0)]
    )

    mock_image_fetch_repo = AsyncMock()
    mock_image_fetch_repo.fetch_image = AsyncMock(
        return_value={"data": b"fake_image_data", "mime_type": "image/jpeg"}
    )

    usecase = ValidateCatImageUseCase(
        mock_image_analysis_service, mock_image_fetch_repo, DEFAULT_VALIDATION_POLICY
    )
    result = await usecase.execute("https://example.com/person.jpg")

    assert result["is_acceptable"] is False
    assert result["reason"] == "person face in the image"


@pytest.mark.asyncio
async def test_execute_moderation_content_detected() -> None:
    """不適切なコンテンツが検出された画像のテスト"""
    mock_image_analysis_service = AsyncMock()
    # 不適切なコンテンツが検出された場合（空リストでない）
    mock_image_analysis_service.detect_moderation_labels = AsyncMock(
        return_value=[ModerationLabelDetection(name="Explicit Nudity", confidence=95.0)]
    )
    mock_image_analysis_service.detect_faces = AsyncMock(return_value=[])
    mock_image_analysis_service.detect_labels = AsyncMock(
        return_value=[LabelDetection(name="Cat", confidence=95.0)]
    )

    mock_image_fetch_repo = AsyncMock()
    mock_image_fetch_repo.fetch_image = AsyncMock(
        return_value={"data": b"fake_image_data", "mime_type": "image/jpeg"}
    )

    usecase = ValidateCatImageUseCase(
        mock_image_analysis_service, mock_image_fetch_repo, DEFAULT_VALIDATION_POLICY
    )
    result = await usecase.execute("https://example.com/nsfw.jpg")

    assert result["is_acceptable"] is False
    assert result["reason"] == "not moderation image"


@pytest.mark.asyncio
async def test_execute_image_fetch_failed() -> None:
    """画像取得失敗時は例外が伝播することをテスト"""
    mock_image_analysis_service = AsyncMock()
    mock_image_fetch_repo = AsyncMock()
    mock_image_fetch_repo.fetch_image = AsyncMock(
        side_effect=ErrImageFetchFailed("Failed to fetch image")
    )

    usecase = ValidateCatImageUseCase(
        mock_image_analysis_service, mock_image_fetch_repo, DEFAULT_VALIDATION_POLICY
    )

    # 画像取得エラーはUseCaseでキャッチせずController層に伝播する
    with pytest.raises(ErrImageFetchFailed):
        await usecase.execute("https://example.com/invalid.jpg")


@pytest.mark.asyncio
async def test_execute_with_custom_policy() -> None:
    """カスタムポリシーでのテスト"""
    custom_policy: CatImageValidationPolicy = {
        "moderation_min_confidence": 50.0,
        "face_detection_min_confidence": 90.0,
        "cat_label_min_confidence": 70.0,
        "labels_max_count": 10,
        "labels_min_confidence": 75.0,
    }

    mock_image_analysis_service = AsyncMock()
    mock_image_analysis_service.detect_moderation_labels = AsyncMock(return_value=[])
    mock_image_analysis_service.detect_faces = AsyncMock(return_value=[])
    # 信頼度75.0の猫ラベル（カスタムポリシーでは70.0超でOK）
    mock_image_analysis_service.detect_labels = AsyncMock(
        return_value=[LabelDetection(name="Cat", confidence=75.0)]
    )

    mock_image_fetch_repo = AsyncMock()
    mock_image_fetch_repo.fetch_image = AsyncMock(
        return_value={"data": b"fake_image_data", "mime_type": "image/jpeg"}
    )

    usecase = ValidateCatImageUseCase(
        mock_image_analysis_service, mock_image_fetch_repo, custom_policy
    )
    result = await usecase.execute("https://example.com/cat.jpg")

    assert result["is_acceptable"] is True


@pytest.mark.asyncio
async def test_execute_cat_confidence_too_low() -> None:
    """猫ラベルの信頼度が低い画像のテスト"""
    mock_image_analysis_service = AsyncMock()
    mock_image_analysis_service.detect_moderation_labels = AsyncMock(return_value=[])
    mock_image_analysis_service.detect_faces = AsyncMock(return_value=[])
    # 信頼度80.0の猫ラベル（80.0超でないとNG）
    mock_image_analysis_service.detect_labels = AsyncMock(
        return_value=[LabelDetection(name="Cat", confidence=80.0)]
    )

    mock_image_fetch_repo = AsyncMock()
    mock_image_fetch_repo.fetch_image = AsyncMock(
        return_value={"data": b"fake_image_data", "mime_type": "image/jpeg"}
    )

    usecase = ValidateCatImageUseCase(
        mock_image_analysis_service, mock_image_fetch_repo, DEFAULT_VALIDATION_POLICY
    )
    result = await usecase.execute("https://example.com/cat.jpg")

    assert result["is_acceptable"] is False
    assert result["reason"] == "not cat image"


@pytest.mark.asyncio
async def test_execute_face_confidence_borderline() -> None:
    """顔検出の信頼度がボーダーラインの画像のテスト"""
    mock_image_analysis_service = AsyncMock()
    mock_image_analysis_service.detect_moderation_labels = AsyncMock(return_value=[])
    # 信頼度96.0の顔を検出（96.0超でないとNG、これはOK）
    mock_image_analysis_service.detect_faces = AsyncMock(
        return_value=[FaceDetection(confidence=96.0)]
    )
    mock_image_analysis_service.detect_labels = AsyncMock(
        return_value=[LabelDetection(name="Cat", confidence=95.0)]
    )

    mock_image_fetch_repo = AsyncMock()
    mock_image_fetch_repo.fetch_image = AsyncMock(
        return_value={"data": b"fake_image_data", "mime_type": "image/jpeg"}
    )

    usecase = ValidateCatImageUseCase(
        mock_image_analysis_service, mock_image_fetch_repo, DEFAULT_VALIDATION_POLICY
    )
    result = await usecase.execute("https://example.com/cat.jpg")

    # 96.0は96.0超ではないのでOK
    assert result["is_acceptable"] is True


@pytest.mark.asyncio
async def test_execute_multiple_labels_with_cat() -> None:
    """複数のラベルがあり、その中に猫が含まれる画像のテスト"""
    mock_image_analysis_service = AsyncMock()
    mock_image_analysis_service.detect_moderation_labels = AsyncMock(return_value=[])
    mock_image_analysis_service.detect_faces = AsyncMock(return_value=[])
    mock_image_analysis_service.detect_labels = AsyncMock(
        return_value=[
            LabelDetection(name="Animal", confidence=98.0),
            LabelDetection(name="Mammal", confidence=96.0),
            LabelDetection(name="Cat", confidence=95.0),
            LabelDetection(name="Pet", confidence=92.0),
        ]
    )

    mock_image_fetch_repo = AsyncMock()
    mock_image_fetch_repo.fetch_image = AsyncMock(
        return_value={"data": b"fake_image_data", "mime_type": "image/jpeg"}
    )

    usecase = ValidateCatImageUseCase(
        mock_image_analysis_service, mock_image_fetch_repo, DEFAULT_VALIDATION_POLICY
    )
    result = await usecase.execute("https://example.com/cat.jpg")

    assert result["is_acceptable"] is True
