# 絶対厳守：編集前に必ずAI実装ルールを読む

from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

from domain.create_lgtm_image import can_convert_image_extension


class LgtmImageCreateRequest(BaseModel):
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


class LgtmImageCreateFromUrlRequest(BaseModel):
    image_url: str = Field(
        ...,
        alias="imageUrl",
        description=(
            "画像のURL(httpsのみ許可)。"
            "URLの形式・スキームを検証します。"
            "許可ドメインのチェックは infrastructure 層で実施します。"
        ),
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


class TextSearchRequest(BaseModel):
    query: str = Field(
        ...,
        description="検索クエリテキスト",
        min_length=1,
        max_length=200,
        examples=["猫", "おめでとう", "ありがとう"],
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        # 空白のみの文字列をチェック
        if not v.strip():
            raise ValueError("検索クエリは空白のみにできません")
        return v


class LgtmImageSearchByImageRequest(BaseModel):
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


class LgtmImageSearchByImageFromUrlRequest(BaseModel):
    image_url: str = Field(
        ...,
        alias="imageUrl",
        description=("画像のURL(httpsのみ許可)。"),
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
