# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Protocol, Required, TypedDict


class FaceDetection(TypedDict):
    confidence: Required[float]


class LabelDetection(TypedDict):
    name: Required[str]
    confidence: Required[float]


class ModerationLabelDetection(TypedDict):
    name: Required[str]
    confidence: Required[float]


class ImageAnalysisServiceInterface(Protocol):
    async def detect_moderation_labels(
        self, image_bytes: bytes, min_confidence: float
    ) -> list[ModerationLabelDetection]: ...

    async def detect_faces(self, image_bytes: bytes) -> list[FaceDetection]: ...

    async def detect_labels(
        self, image_bytes: bytes, max_labels: int, min_confidence: float
    ) -> list[LabelDetection]: ...

    async def detect_moderation_labels_from_s3(
        self, bucket: str, key: str, min_confidence: float
    ) -> list[ModerationLabelDetection]: ...

    async def detect_faces_from_s3(
        self, bucket: str, key: str
    ) -> list[FaceDetection]: ...

    async def detect_labels_from_s3(
        self, bucket: str, key: str, max_labels: int, min_confidence: float
    ) -> list[LabelDetection]: ...
