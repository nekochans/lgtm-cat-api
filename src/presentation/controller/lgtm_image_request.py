# 絶対厳守：編集前に必ずAI実装ルールを読む

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.domain.create_lgtm_image import can_convert_image_extension


class LgtmImageCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    image: str = Field(
        ...,
        description="base64エンコードされた画像データ",
        examples=["iVBORw0KGgoAAAANSUhEUgAAAAUA..."],
    )
    image_extension: str = Field(
        ...,
        alias="imageExtension",
        description="画像拡張子",
        examples=[".png", ".jpg", ".jpeg"],
    )

    @field_validator("image_extension")
    @classmethod
    def validate_image_extension(cls, v: str) -> str:
        if not can_convert_image_extension(v):
            raise ValueError(f"Invalid image extension: {v}")
        return v
