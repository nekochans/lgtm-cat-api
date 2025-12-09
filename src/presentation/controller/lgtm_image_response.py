# 絶対厳守：編集前に必ずAI実装ルールを読む

from pydantic import BaseModel, Field, HttpUrl


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
    lgtm_images: list[LgtmImageItem] = Field(
        ...,
        serialization_alias="lgtmImages",
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
    lgtm_images: list[LgtmImageItem] = Field(
        ...,
        serialization_alias="lgtmImages",
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
    image_url: HttpUrl = Field(
        ...,
        serialization_alias="imageUrl",
        description="アップロードされた画像のURL",
        examples=[
            "https://lgtm-images.lgtmeow.com/2024/01/15/14/5947f291-a46e-453c-a230-0d756d7174cb.webp"
        ],
    )


class LgtmImageSearchResponse(BaseModel):
    lgtm_images: list["LgtmImageSearchItem"] = Field(
        ...,
        serialization_alias="lgtmImages",
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
        serialization_alias="similarityScore",
        description="類似度スコア(0.0〜1.0)",
        examples=[0.95],
    )


class LgtmImageSearchByImageResponse(BaseModel):
    lgtm_images: list[LgtmImageSearchItem] = Field(
        ...,
        serialization_alias="lgtmImages",
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


class LgtmImageMarkdownResponse(BaseModel):
    markdown: str = Field(
        ...,
        description="LGTM画像のマークダウン形式",
        examples=[
            "[![LGTMeow](https://lgtm-images.lgtmeow.com/2022/03/23/10/9738095a-f426-48e4-be8d-93f933c42917.webp)](https://lgtmeow.com)"
        ],
    )
