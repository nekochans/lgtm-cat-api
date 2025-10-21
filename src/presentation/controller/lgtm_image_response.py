# 絶対厳守：編集前に必ずAI実装ルールを読む

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class LgtmImageItem(BaseModel):
    id: str = Field(..., description="LGTM画像の一意識別子", examples=["1"])
    url: HttpUrl = Field(
        ...,
        description="LGTM画像のURL",
    )


class LgtmImageRandomListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lgtm_images: list[LgtmImageItem] = Field(
        ..., alias="LgtmImages", description="LGTM画像のリスト"
    )


class LgtmImageRecentlyCreatedListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lgtm_images: list[LgtmImageItem] = Field(
        ..., alias="LgtmImages", description="最近作成されたLGTM画像のリスト"
    )
