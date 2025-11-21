# 絶対厳守：編集前に必ずAI実装ルールを読む

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class LgtmImageItem(BaseModel):
    id: str = Field(..., description="LGTM画像の一意識別子", examples=["1"])
    url: HttpUrl = Field(
        ...,
        description="LGTM画像のURL",
        examples=[
            "https://lgtm-images.lgtmeow.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp"
        ],
    )


class LgtmImageRandomListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lgtm_images: list[LgtmImageItem] = Field(
        ...,
        alias="lgtmImages",
        description="LGTM画像のリスト",
        examples=[
            [
                {
                    "id": "1",
                    "url": "https://lgtm-images.lgtmeow.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp",
                },
                {
                    "id": "2",
                    "url": "https://lgtm-images.lgtmeow.com/2021/03/16/23/6947f291-a46e-453c-a230-0d756d7174cb.webp",
                },
            ]
        ],
    )


class LgtmImageRecentlyCreatedListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lgtm_images: list[LgtmImageItem] = Field(
        ...,
        alias="lgtmImages",
        description="最近作成されたLGTM画像のリスト",
        examples=[
            [
                {
                    "id": "1",
                    "url": "https://lgtm-images.lgtmeow.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp",
                },
                {
                    "id": "2",
                    "url": "https://lgtm-images.lgtmeow.com/2021/03/16/23/6947f291-a46e-453c-a230-0d756d7174cb.webp",
                },
            ]
        ],
    )


class LgtmImageCreateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    image_url: HttpUrl = Field(
        ...,
        alias="imageUrl",
        description="アップロードされた画像のURL",
        examples=[
            "https://lgtm-images.lgtmeow.com/2024/01/15/14/5947f291-a46e-453c-a230-0d756d7174cb.webp"
        ],
    )


class LgtmImageSearchResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lgtm_images: list["LgtmImageSearchItem"] = Field(
        ...,
        alias="lgtmImages",
        description="検索結果の画像リスト",
        examples=[
            [
                {
                    "id": "1",
                    "url": "https://lgtm-images.lgtmeow.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp",
                    "similarityScore": 0.9,
                },
                {
                    "id": "2",
                    "url": "https://lgtm-images.lgtmeow.com/2021/03/16/23/6947f291-a46e-453c-a230-0d756d7174cb.webp",
                    "similarityScore": 0.8,
                },
            ]
        ],
    )


class LgtmImageSearchItem(BaseModel):
    id: str = Field(..., description="画像ID", examples=["1"])
    url: HttpUrl = Field(
        ...,
        description="画像URL",
        examples=[
            "https://lgtm-images.lgtmeow.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp"
        ],
    )
    similarity_score: float = Field(
        ...,
        alias="similarityScore",
        description="類似度スコア（0.0〜1.0）",
        examples=[0.95],
    )


class LgtmImageSearchByImageResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lgtm_images: list[LgtmImageSearchItem] = Field(
        ...,
        alias="lgtmImages",
        description="類似画像検索結果のリスト",
        examples=[
            [
                {
                    "id": "1",
                    "url": "https://lgtm-images.lgtmeow.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp",
                    "similarityScore": 0.95,
                },
                {
                    "id": "2",
                    "url": "https://lgtm-images.lgtmeow.com/2021/03/16/23/6947f291-a46e-453c-a230-0d756d7174cb.webp",
                    "similarityScore": 0.87,
                },
            ]
        ],
    )
