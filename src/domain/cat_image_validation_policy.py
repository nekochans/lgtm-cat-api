# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Final, NotRequired, Required, TypedDict


class CatImageValidationPolicy(TypedDict):
    moderation_min_confidence: Required[float]
    face_detection_min_confidence: Required[float]
    cat_label_min_confidence: Required[float]
    labels_max_count: Required[int]
    labels_min_confidence: Required[float]


DEFAULT_VALIDATION_POLICY: Final[CatImageValidationPolicy] = {
    "moderation_min_confidence": 40.0,  # 不適切コンテンツの最小信頼度
    "face_detection_min_confidence": 96.0,  # 人の顔検出の最小信頼度
    "cat_label_min_confidence": 80.0,  # 猫ラベルの最小信頼度
    "labels_max_count": 10,  # ラベル検出の最大数
    "labels_min_confidence": 75.0,  # ラベル検出の最小信頼度
}


class CatImageValidationResult(TypedDict):
    is_acceptable: Required[bool]
    reason: NotRequired[str]
