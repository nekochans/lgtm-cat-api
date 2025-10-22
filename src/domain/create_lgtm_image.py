# 絶対厳守：編集前に必ずAI実装ルールを読む

from datetime import datetime, timezone
from typing import Required, TypedDict


class UploadedLgtmImage(TypedDict):
    url: Required[str]


class UploadObjectStorageDto(TypedDict):
    body: Required[bytes]
    image_extension: Required[str]
    key: Required[str]


def can_convert_image_extension(ext: str) -> bool:
    return ext in {".png", ".jpg", ".jpeg"}


def build_object_prefix(dt: datetime) -> str:
    from datetime import timedelta

    jst = timezone(timedelta(hours=9))
    dt_tokyo = dt.astimezone(jst)

    # 日本時間でフォーマット（YYYY/MM/DD/HH/）
    return dt_tokyo.strftime("%Y/%m/%d/%H/")


def create_upload_object_strage_dto(
    body: bytes, prefix: str, image_name: str, image_extension: str
) -> UploadObjectStorageDto:
    upload_key = f"{prefix}{image_name}{image_extension}"

    return UploadObjectStorageDto(
        body=body,
        image_extension=image_extension,
        key=upload_key,
    )


def create_uploaded_lgtm_image(
    domain: str, prefix: str, image_name: str
) -> UploadedLgtmImage:
    url = f"https://{domain}/{prefix}{image_name}.webp"

    return UploadedLgtmImage(url=url)
