# 絶対厳守：編集前に必ずAI実装ルールを読む
from typing import Required, TypedDict

from src.domain.lgtm_image import LgtmImage, LgtmImageId


class LgtmImageObject(TypedDict):
    id: Required[LgtmImageId]
    path: Required[str]
    filename: Required[str]


def create_lgtm_image(lgtm_image_object: LgtmImageObject, base_url: str) -> LgtmImage:
    return LgtmImage(
        id=str(lgtm_image_object["id"]),
        url=f"https://{base_url}/{lgtm_image_object['path']}/{lgtm_image_object['filename']}",
    )
