# 絶対厳守：編集前に必ずAI実装ルールを読む

import aioboto3
from botocore.exceptions import BotoCoreError, ClientError

from domain.lgtm_image_errors import ErrRekognitionFailed
from domain.image_analysis_interface import (
    FaceDetection,
    LabelDetection,
    ModerationLabelDetection,
    ImageAnalysisServiceInterface,
)


class RekognitionImageAnalysisService(ImageAnalysisServiceInterface):
    def __init__(self, region: str) -> None:
        self.region = region
        self.session = aioboto3.Session()

    async def detect_moderation_labels(
        self, image_bytes: bytes, min_confidence: float
    ) -> list[ModerationLabelDetection]:
        try:
            async with self.session.client(
                "rekognition", region_name=self.region
            ) as client:
                response = await client.detect_moderation_labels(
                    Image={"Bytes": image_bytes}, MinConfidence=min_confidence
                )
                # AWS Rekognitionのレスポンスをドメイン型に変換
                return [
                    ModerationLabelDetection(
                        name=label["Name"],
                        confidence=label["Confidence"],
                    )
                    for label in response.get("ModerationLabels", [])
                ]
        except (BotoCoreError, ClientError) as e:
            raise ErrRekognitionFailed(f"DetectModerationLabels failed: {e}") from e
        except Exception as e:
            raise ErrRekognitionFailed(
                f"Unexpected error in DetectModerationLabels: {e}"
            ) from e

    async def detect_faces(self, image_bytes: bytes) -> list[FaceDetection]:
        try:
            async with self.session.client(
                "rekognition", region_name=self.region
            ) as client:
                response = await client.detect_faces(Image={"Bytes": image_bytes})
                # AWS Rekognitionのレスポンスをドメイン型に変換
                return [
                    FaceDetection(confidence=face["Confidence"])
                    for face in response.get("FaceDetails", [])
                ]
        except (BotoCoreError, ClientError) as e:
            raise ErrRekognitionFailed(f"DetectFaces failed: {e}") from e
        except Exception as e:
            raise ErrRekognitionFailed(f"Unexpected error in DetectFaces: {e}") from e

    async def detect_labels(
        self, image_bytes: bytes, max_labels: int, min_confidence: float
    ) -> list[LabelDetection]:
        try:
            async with self.session.client(
                "rekognition", region_name=self.region
            ) as client:
                response = await client.detect_labels(
                    Image={"Bytes": image_bytes},
                    MaxLabels=max_labels,
                    MinConfidence=min_confidence,
                )
                # AWS Rekognitionのレスポンスをドメイン型に変換
                return [
                    LabelDetection(name=label["Name"], confidence=label["Confidence"])
                    for label in response.get("Labels", [])
                ]
        except (BotoCoreError, ClientError) as e:
            raise ErrRekognitionFailed(f"DetectLabels failed: {e}") from e
        except Exception as e:
            raise ErrRekognitionFailed(f"Unexpected error in DetectLabels: {e}") from e

    async def detect_moderation_labels_from_s3(
        self, bucket: str, key: str, min_confidence: float
    ) -> list[ModerationLabelDetection]:
        try:
            async with self.session.client(
                "rekognition", region_name=self.region
            ) as client:
                response = await client.detect_moderation_labels(
                    Image={"S3Object": {"Bucket": bucket, "Name": key}},
                    MinConfidence=min_confidence,
                )
                return [
                    ModerationLabelDetection(
                        name=label["Name"],
                        confidence=label["Confidence"],
                    )
                    for label in response.get("ModerationLabels", [])
                ]
        except (BotoCoreError, ClientError) as e:
            raise ErrRekognitionFailed(
                f"DetectModerationLabels from S3 failed: {e}"
            ) from e
        except Exception as e:
            raise ErrRekognitionFailed(
                f"Unexpected error in DetectModerationLabels from S3: {e}"
            ) from e

    async def detect_faces_from_s3(self, bucket: str, key: str) -> list[FaceDetection]:
        try:
            async with self.session.client(
                "rekognition", region_name=self.region
            ) as client:
                response = await client.detect_faces(
                    Image={"S3Object": {"Bucket": bucket, "Name": key}}
                )
                return [
                    FaceDetection(confidence=face["Confidence"])
                    for face in response.get("FaceDetails", [])
                ]
        except (BotoCoreError, ClientError) as e:
            raise ErrRekognitionFailed(f"DetectFaces from S3 failed: {e}") from e
        except Exception as e:
            raise ErrRekognitionFailed(
                f"Unexpected error in DetectFaces from S3: {e}"
            ) from e

    async def detect_labels_from_s3(
        self, bucket: str, key: str, max_labels: int, min_confidence: float
    ) -> list[LabelDetection]:
        try:
            async with self.session.client(
                "rekognition", region_name=self.region
            ) as client:
                response = await client.detect_labels(
                    Image={"S3Object": {"Bucket": bucket, "Name": key}},
                    MaxLabels=max_labels,
                    MinConfidence=min_confidence,
                )
                return [
                    LabelDetection(name=label["Name"], confidence=label["Confidence"])
                    for label in response.get("Labels", [])
                ]
        except (BotoCoreError, ClientError) as e:
            raise ErrRekognitionFailed(f"DetectLabels from S3 failed: {e}") from e
        except Exception as e:
            raise ErrRekognitionFailed(
                f"Unexpected error in DetectLabels from S3: {e}"
            ) from e
