# 絶対厳守：編集前に必ずAI実装ルールを読む
from unittest.mock import AsyncMock, patch

import pytest
from botocore.exceptions import ClientError

from domain.lgtm_image_errors import ErrRekognitionFailed
from domain.image_analysis_types import (
    FaceDetection,
    LabelDetection,
    ModerationLabelDetection,
)
from infrastructure.rekognition_client import RekognitionClient


@pytest.mark.asyncio
async def test_detect_moderation_labels_success() -> None:
    """DetectModerationLabels成功時のテスト"""
    client = RekognitionClient(region="ap-northeast-1")

    with patch.object(client.session, "client") as mock_client:
        mock_rekognition = AsyncMock()
        mock_rekognition.detect_moderation_labels = AsyncMock(
            return_value={"ModerationLabels": []}
        )
        mock_client.return_value.__aenter__.return_value = mock_rekognition

        result = await client.detect_moderation_labels(b"fake_image_data", 40.0)

        assert result == []
        mock_rekognition.detect_moderation_labels.assert_called_once_with(
            Image={"Bytes": b"fake_image_data"}, MinConfidence=40.0
        )


@pytest.mark.asyncio
async def test_detect_moderation_labels_with_labels() -> None:
    """DetectModerationLabels: ラベルが検出された場合のテスト"""
    client = RekognitionClient(region="ap-northeast-1")

    # AWS Rekognitionからのレスポンス（dict形式）
    aws_response_labels = [
        {"Name": "Violence", "Confidence": 85.5},
        {"Name": "Suggestive", "Confidence": 60.2},
    ]

    # 期待される戻り値（ModerationLabelDetection形式）
    expected_labels = [
        ModerationLabelDetection(name="Violence", confidence=85.5),
        ModerationLabelDetection(name="Suggestive", confidence=60.2),
    ]

    with patch.object(client.session, "client") as mock_client:
        mock_rekognition = AsyncMock()
        mock_rekognition.detect_moderation_labels = AsyncMock(
            return_value={"ModerationLabels": aws_response_labels}
        )
        mock_client.return_value.__aenter__.return_value = mock_rekognition

        result = await client.detect_moderation_labels(b"fake_image_data", 50.0)

        assert result == expected_labels
        mock_rekognition.detect_moderation_labels.assert_called_once_with(
            Image={"Bytes": b"fake_image_data"}, MinConfidence=50.0
        )


@pytest.mark.asyncio
async def test_detect_moderation_labels_failure() -> None:
    """DetectModerationLabels失敗時のテスト"""
    client = RekognitionClient(region="ap-northeast-1")

    with patch.object(client.session, "client") as mock_client:
        mock_rekognition = AsyncMock()
        error_response = {
            "Error": {"Code": "InvalidParameterException", "Message": "API Error"}
        }
        mock_rekognition.detect_moderation_labels = AsyncMock(
            side_effect=ClientError(error_response, "DetectModerationLabels")  # type: ignore[arg-type]
        )
        mock_client.return_value.__aenter__.return_value = mock_rekognition

        with pytest.raises(ErrRekognitionFailed) as exc_info:
            await client.detect_moderation_labels(b"fake_image_data", 40.0)

        assert "DetectModerationLabels failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_detect_moderation_labels_unexpected_exception() -> None:
    """DetectModerationLabels予期しない例外のテスト"""
    client = RekognitionClient(region="ap-northeast-1")

    with patch.object(client.session, "client") as mock_client:
        mock_rekognition = AsyncMock()
        # 予期しない例外を発生させる
        mock_rekognition.detect_moderation_labels = AsyncMock(
            side_effect=RuntimeError("Unexpected runtime error")
        )
        mock_client.return_value.__aenter__.return_value = mock_rekognition

        with pytest.raises(ErrRekognitionFailed) as exc_info:
            await client.detect_moderation_labels(b"fake_image_data", 40.0)

        assert "Unexpected error in DetectModerationLabels" in str(exc_info.value)


@pytest.mark.asyncio
async def test_detect_faces_success() -> None:
    """DetectFaces成功時のテスト"""
    client = RekognitionClient(region="ap-northeast-1")

    with patch.object(client.session, "client") as mock_client:
        mock_rekognition = AsyncMock()
        mock_rekognition.detect_faces = AsyncMock(return_value={"FaceDetails": []})
        mock_client.return_value.__aenter__.return_value = mock_rekognition

        result = await client.detect_faces(b"fake_image_data")

        assert result == []
        mock_rekognition.detect_faces.assert_called_once_with(
            Image={"Bytes": b"fake_image_data"}
        )


@pytest.mark.asyncio
async def test_detect_faces_with_faces() -> None:
    """DetectFaces: 顔が検出された場合のテスト"""
    client = RekognitionClient(region="ap-northeast-1")

    # AWS Rekognitionのレスポンス形式
    aws_faces = [
        {"Confidence": 99.5, "BoundingBox": {}},
        {"Confidence": 98.2, "BoundingBox": {}},
    ]

    # 期待されるドメイン型の結果
    expected_result: list[FaceDetection] = [
        FaceDetection(confidence=99.5),
        FaceDetection(confidence=98.2),
    ]

    with patch.object(client.session, "client") as mock_client:
        mock_rekognition = AsyncMock()
        mock_rekognition.detect_faces = AsyncMock(
            return_value={"FaceDetails": aws_faces}
        )
        mock_client.return_value.__aenter__.return_value = mock_rekognition

        result = await client.detect_faces(b"fake_image_data")

        assert result == expected_result
        # Rekognition APIが正しいパラメータで呼び出されたことを検証
        mock_rekognition.detect_faces.assert_awaited_once_with(
            Image={"Bytes": b"fake_image_data"}
        )


@pytest.mark.asyncio
async def test_detect_faces_failure() -> None:
    """DetectFaces失敗時のテスト"""
    client = RekognitionClient(region="ap-northeast-1")

    with patch.object(client.session, "client") as mock_client:
        mock_rekognition = AsyncMock()
        error_response = {
            "Error": {"Code": "InvalidParameterException", "Message": "API Error"}
        }
        mock_rekognition.detect_faces = AsyncMock(
            side_effect=ClientError(error_response, "DetectFaces")  # type: ignore[arg-type]
        )
        mock_client.return_value.__aenter__.return_value = mock_rekognition

        with pytest.raises(ErrRekognitionFailed) as exc_info:
            await client.detect_faces(b"fake_image_data")

        assert "DetectFaces failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_detect_faces_unexpected_exception() -> None:
    """DetectFaces予期しない例外のテスト"""
    client = RekognitionClient(region="ap-northeast-1")

    with patch.object(client.session, "client") as mock_client:
        mock_rekognition = AsyncMock()
        # 予期しない例外を発生させる
        mock_rekognition.detect_faces = AsyncMock(
            side_effect=ValueError("Unexpected value error")
        )
        mock_client.return_value.__aenter__.return_value = mock_rekognition

        with pytest.raises(ErrRekognitionFailed) as exc_info:
            await client.detect_faces(b"fake_image_data")

        assert "Unexpected error in DetectFaces" in str(exc_info.value)


@pytest.mark.asyncio
async def test_detect_labels_success() -> None:
    """DetectLabels成功時のテスト"""
    client = RekognitionClient(region="ap-northeast-1")

    with patch.object(client.session, "client") as mock_client:
        mock_rekognition = AsyncMock()
        mock_rekognition.detect_labels = AsyncMock(return_value={"Labels": []})
        mock_client.return_value.__aenter__.return_value = mock_rekognition

        result = await client.detect_labels(b"fake_image_data", 10, 75.0)

        assert result == []
        mock_rekognition.detect_labels.assert_called_once_with(
            Image={"Bytes": b"fake_image_data"}, MaxLabels=10, MinConfidence=75.0
        )


@pytest.mark.asyncio
async def test_detect_labels_with_cat() -> None:
    """DetectLabels: 猫ラベルが検出された場合のテスト"""
    client = RekognitionClient(region="ap-northeast-1")

    # AWS Rekognitionのレスポンス形式
    aws_labels = [
        {"Name": "Cat", "Confidence": 95.8},
        {"Name": "Animal", "Confidence": 92.3},
        {"Name": "Pet", "Confidence": 90.1},
    ]

    # 期待されるドメイン型の結果
    expected_result: list[LabelDetection] = [
        LabelDetection(name="Cat", confidence=95.8),
        LabelDetection(name="Animal", confidence=92.3),
        LabelDetection(name="Pet", confidence=90.1),
    ]

    with patch.object(client.session, "client") as mock_client:
        mock_rekognition = AsyncMock()
        mock_rekognition.detect_labels = AsyncMock(return_value={"Labels": aws_labels})
        mock_client.return_value.__aenter__.return_value = mock_rekognition

        result = await client.detect_labels(b"fake_image_data", 5, 80.0)

        assert result == expected_result
        mock_rekognition.detect_labels.assert_called_once_with(
            Image={"Bytes": b"fake_image_data"}, MaxLabels=5, MinConfidence=80.0
        )


@pytest.mark.asyncio
async def test_detect_labels_failure() -> None:
    """DetectLabels失敗時のテスト"""
    client = RekognitionClient(region="ap-northeast-1")

    with patch.object(client.session, "client") as mock_client:
        mock_rekognition = AsyncMock()
        error_response = {
            "Error": {"Code": "InvalidParameterException", "Message": "API Error"}
        }
        mock_rekognition.detect_labels = AsyncMock(
            side_effect=ClientError(error_response, "DetectLabels")  # type: ignore[arg-type]
        )
        mock_client.return_value.__aenter__.return_value = mock_rekognition

        with pytest.raises(ErrRekognitionFailed) as exc_info:
            await client.detect_labels(b"fake_image_data", 10, 75.0)

        assert "DetectLabels failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_detect_labels_unexpected_exception() -> None:
    """DetectLabels予期しない例外のテスト"""
    client = RekognitionClient(region="ap-northeast-1")

    with patch.object(client.session, "client") as mock_client:
        mock_rekognition = AsyncMock()
        # 予期しない例外を発生させる
        mock_rekognition.detect_labels = AsyncMock(
            side_effect=TypeError("Unexpected type error")
        )
        mock_client.return_value.__aenter__.return_value = mock_rekognition

        with pytest.raises(ErrRekognitionFailed) as exc_info:
            await client.detect_labels(b"fake_image_data", 10, 75.0)

        assert "Unexpected error in DetectLabels" in str(exc_info.value)
