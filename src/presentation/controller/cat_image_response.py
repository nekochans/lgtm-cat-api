# 絶対厳守：編集前に必ずAI実装ルールを読む
"""猫画像判定のレスポンスモデル"""

from pydantic import BaseModel, Field


class CatImageValidationResponse(BaseModel):
    """猫画像判定レスポンス"""

    is_acceptable_cat_image: bool = Field(
        ...,
        serialization_alias="isAcceptableCatImage",
        description="受け入れ可能な猫画像かどうか",
        examples=[True, False],
    )
    not_acceptable_reason: str | None = Field(
        None,
        serialization_alias="notAcceptableReason",
        description="受け入れ不可の理由",
        examples=[
            "not cat image",
            "person face in the image",
            "not moderation image",
        ],
    )
