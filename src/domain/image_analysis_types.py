# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Required, TypedDict


class FaceDetection(TypedDict):
    confidence: Required[float]


class LabelDetection(TypedDict):
    name: Required[str]
    confidence: Required[float]


class ModerationLabelDetection(TypedDict):
    name: Required[str]
    confidence: Required[float]
