# 絶対厳守：編集前に必ずAI実装ルールを読む
"""ValidateCatImageFromS3UseCaseのテスト"""

from unittest.mock import AsyncMock

import pytest

from domain.cat_image_validation_policy import (
    CatImageValidationPolicy,
    DEFAULT_VALIDATION_POLICY,
)
from domain.image_analysis_interface import (
    FaceDetection,
    LabelDetection,
    ModerationLabelDetection,
)
from domain.lgtm_image_errors import ErrRekognitionFailed
from usecase.validate_cat_image_from_s3_usecase import ValidateCatImageFromS3UseCase


@pytest.mark.asyncio
async def test_execute_acceptable_cat_image() -> None:
    """受け入れ可能な猫画像のテスト"""
    mock_image_analysis_service = AsyncMock()
    mock_image_analysis_service.detect_moderation_labels_from_s3 = AsyncMock(
        return_value=[]
    )
    mock_image_analysis_service.detect_faces_from_s3 = AsyncMock(return_value=[])
    mock_image_analysis_service.detect_labels_from_s3 = AsyncMock(
        return_value=[LabelDetection(name="Cat", confidence=95.0)]
    )

    usecase = ValidateCatImageFromS3UseCase(
        mock_image_analysis_service, DEFAULT_VALIDATION_POLICY
    )
    result = await usecase.execute("test-bucket", "images/cat.jpg")

    assert result["is_acceptable"] is True
    assert "reason" not in result

    # S3参照版メソッドが正しい引数で呼び出されたことを検証
    mock_image_analysis_service.detect_moderation_labels_from_s3.assert_called_once_with(
        "test-bucket",
        "images/cat.jpg",
        DEFAULT_VALIDATION_POLICY["moderation_min_confidence"],
    )
    mock_image_analysis_service.detect_faces_from_s3.assert_called_once_with(
        "test-bucket", "images/cat.jpg"
    )
    mock_image_analysis_service.detect_labels_from_s3.assert_called_once_with(
        "test-bucket",
        "images/cat.jpg",
        DEFAULT_VALIDATION_POLICY["labels_max_count"],
        DEFAULT_VALIDATION_POLICY["labels_min_confidence"],
    )


@pytest.mark.asyncio
async def test_execute_not_cat_image() -> None:
    """猫が写っていない画像のテスト"""
    mock_image_analysis_service = AsyncMock()
    mock_image_analysis_service.detect_moderation_labels_from_s3 = AsyncMock(
        return_value=[]
    )
    mock_image_analysis_service.detect_faces_from_s3 = AsyncMock(return_value=[])
    mock_image_analysis_service.detect_labels_from_s3 = AsyncMock(
        return_value=[LabelDetection(name="Dog", confidence=95.0)]
    )

    usecase = ValidateCatImageFromS3UseCase(
        mock_image_analysis_service, DEFAULT_VALIDATION_POLICY
    )
    result = await usecase.execute("test-bucket", "images/dog.jpg")

    assert result["is_acceptable"] is False
    assert result["reason"] == "not cat image"


@pytest.mark.asyncio
async def test_execute_person_face_detected() -> None:
    """人の顔が検出された画像のテスト"""
    mock_image_analysis_service = AsyncMock()
    mock_image_analysis_service.detect_moderation_labels_from_s3 = AsyncMock(
        return_value=[]
    )
    # 信頼度97.0の顔を検出（96.0超でNG）
    mock_image_analysis_service.detect_faces_from_s3 = AsyncMock(
        return_value=[FaceDetection(confidence=97.0)]
    )
    mock_image_analysis_service.detect_labels_from_s3 = AsyncMock(
        return_value=[LabelDetection(name="Cat", confidence=95.0)]
    )

    usecase = ValidateCatImageFromS3UseCase(
        mock_image_analysis_service, DEFAULT_VALIDATION_POLICY
    )
    result = await usecase.execute("test-bucket", "images/person.jpg")

    assert result["is_acceptable"] is False
    assert result["reason"] == "person face in the image"


@pytest.mark.asyncio
async def test_execute_moderation_content_detected() -> None:
    """不適切なコンテンツが検出された画像のテスト"""
    mock_image_analysis_service = AsyncMock()
    # 不適切なコンテンツが検出された場合（空リストでない）
    mock_image_analysis_service.detect_moderation_labels_from_s3 = AsyncMock(
        return_value=[ModerationLabelDetection(name="Explicit Nudity", confidence=95.0)]
    )
    mock_image_analysis_service.detect_faces_from_s3 = AsyncMock(return_value=[])
    mock_image_analysis_service.detect_labels_from_s3 = AsyncMock(
        return_value=[LabelDetection(name="Cat", confidence=95.0)]
    )

    usecase = ValidateCatImageFromS3UseCase(
        mock_image_analysis_service, DEFAULT_VALIDATION_POLICY
    )
    result = await usecase.execute("test-bucket", "images/nsfw.jpg")

    assert result["is_acceptable"] is False
    assert result["reason"] == "not moderation image"


@pytest.mark.asyncio
async def test_execute_rekognition_failed() -> None:
    """Rekognitionサービス障害時は例外が伝播することをテスト"""
    mock_image_analysis_service = AsyncMock()
    mock_image_analysis_service.detect_moderation_labels_from_s3 = AsyncMock(
        side_effect=ErrRekognitionFailed("S3 object not found")
    )

    usecase = ValidateCatImageFromS3UseCase(
        mock_image_analysis_service, DEFAULT_VALIDATION_POLICY
    )

    # RekognitionエラーはキャッチせずController層に伝播する
    with pytest.raises(ErrRekognitionFailed):
        await usecase.execute("test-bucket", "images/invalid.jpg")


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
    mock_image_analysis_service.detect_moderation_labels_from_s3 = AsyncMock(
        return_value=[]
    )
    mock_image_analysis_service.detect_faces_from_s3 = AsyncMock(return_value=[])
    # 信頼度75.0の猫ラベル（カスタムポリシーでは70.0超でOK）
    mock_image_analysis_service.detect_labels_from_s3 = AsyncMock(
        return_value=[LabelDetection(name="Cat", confidence=75.0)]
    )

    usecase = ValidateCatImageFromS3UseCase(mock_image_analysis_service, custom_policy)
    result = await usecase.execute("test-bucket", "images/cat.jpg")

    assert result["is_acceptable"] is True


@pytest.mark.asyncio
async def test_execute_cat_confidence_too_low() -> None:
    """猫ラベルの信頼度が低い画像のテスト"""
    mock_image_analysis_service = AsyncMock()
    mock_image_analysis_service.detect_moderation_labels_from_s3 = AsyncMock(
        return_value=[]
    )
    mock_image_analysis_service.detect_faces_from_s3 = AsyncMock(return_value=[])
    # 信頼度80.0の猫ラベル（80.0超でないとNG）
    mock_image_analysis_service.detect_labels_from_s3 = AsyncMock(
        return_value=[LabelDetection(name="Cat", confidence=80.0)]
    )

    usecase = ValidateCatImageFromS3UseCase(
        mock_image_analysis_service, DEFAULT_VALIDATION_POLICY
    )
    result = await usecase.execute("test-bucket", "images/cat.jpg")

    assert result["is_acceptable"] is False
    assert result["reason"] == "not cat image"


@pytest.mark.asyncio
async def test_execute_face_confidence_borderline() -> None:
    """顔検出の信頼度がボーダーラインの画像のテスト"""
    mock_image_analysis_service = AsyncMock()
    mock_image_analysis_service.detect_moderation_labels_from_s3 = AsyncMock(
        return_value=[]
    )
    # 信頼度96.0の顔を検出（96.0超でないとNG、これはOK）
    mock_image_analysis_service.detect_faces_from_s3 = AsyncMock(
        return_value=[FaceDetection(confidence=96.0)]
    )
    mock_image_analysis_service.detect_labels_from_s3 = AsyncMock(
        return_value=[LabelDetection(name="Cat", confidence=95.0)]
    )

    usecase = ValidateCatImageFromS3UseCase(
        mock_image_analysis_service, DEFAULT_VALIDATION_POLICY
    )
    result = await usecase.execute("test-bucket", "images/cat.jpg")

    # 96.0は96.0超ではないのでOK
    assert result["is_acceptable"] is True


@pytest.mark.asyncio
async def test_execute_multiple_labels_with_cat() -> None:
    """複数のラベルがあり、その中に猫が含まれる画像のテスト"""
    mock_image_analysis_service = AsyncMock()
    mock_image_analysis_service.detect_moderation_labels_from_s3 = AsyncMock(
        return_value=[]
    )
    mock_image_analysis_service.detect_faces_from_s3 = AsyncMock(return_value=[])
    mock_image_analysis_service.detect_labels_from_s3 = AsyncMock(
        return_value=[
            LabelDetection(name="Animal", confidence=98.0),
            LabelDetection(name="Mammal", confidence=96.0),
            LabelDetection(name="Cat", confidence=95.0),
            LabelDetection(name="Pet", confidence=92.0),
        ]
    )

    usecase = ValidateCatImageFromS3UseCase(
        mock_image_analysis_service, DEFAULT_VALIDATION_POLICY
    )
    result = await usecase.execute("test-bucket", "images/cat.jpg")

    assert result["is_acceptable"] is True
