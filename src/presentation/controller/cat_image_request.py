# 絶対厳守：編集前に必ずAI実装ルールを読む
"""猫画像判定のリクエストモデル"""

from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class CatImageValidationFromUrlRequest(BaseModel):
    """URLからの猫画像判定リクエスト"""

    image_url: str = Field(
        ...,
        alias="imageUrl",
        description="画像のURL(httpsのみ許可)。",
        examples=[
            "https://allowed-bucket.r2.cloudflarestorage.com/image.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256",
        ],
        min_length=1,
    )

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, v: str) -> str:
        parsed = urlparse(v)

        # httpsのみ許可
        if parsed.scheme != "https":
            raise ValueError("image_url must be https URL")

        # ホスト名が存在することを確認
        if not parsed.netloc:
            raise ValueError("image_url must have a valid hostname")

        return v


class CatImageValidationFromS3Request(BaseModel):
    """S3オブジェクト参照での猫画像判定リクエスト"""

    bucket_name: str = Field(
        ...,
        alias="bucketName",
        description="S3バケット名",
        examples=["my-bucket"],
        min_length=3,
        max_length=63,
    )

    object_key: str = Field(
        ...,
        alias="objectKey",
        description="S3オブジェクトキー",
        examples=["images/cat.jpg"],
        min_length=1,
        max_length=1024,
    )
