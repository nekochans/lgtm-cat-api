# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from config import (
    get_image_fetch_timeout,
    get_lgtm_images_base_url,
    get_max_image_size,
    get_image_allowed_domain,
    get_upload_s3_bucket_name,
)
from domain.repository.image_fetch_repository_interface import (
    ImageFetchRepositoryInterface,
)
from domain.repository.object_storage_repository_interface import (
    ObjectStorageRepositoryInterface,
)
from infrastructure.repository.http_image_fetch_repository import (
    HttpImageFetchRepository,
)
from infrastructure.s3_repository import S3Repository
from presentation.controller.lgtm_image_controller import LgtmImageController
from presentation.controller.lgtm_image_request import (
    LgtmImageCreateFromUrlRequest,
)
from presentation.dependencies.auth import verify_token

router = APIRouter()


def create_image_fetch_repository(
    timeout: int = Depends(get_image_fetch_timeout),
    max_size: int = Depends(get_max_image_size),
    allowed_domain: str = Depends(get_image_allowed_domain),
) -> ImageFetchRepositoryInterface:
    return HttpImageFetchRepository(
        timeout=timeout, max_size=max_size, allowed_domain=allowed_domain
    )


def create_object_storage_repository(
    bucket_name: str = Depends(get_upload_s3_bucket_name),
) -> ObjectStorageRepositoryInterface:
    return S3Repository(bucket_name)


@router.post(
    "/v2/lgtm-images",
    summary="署名付きURLからLGTM画像を作成",
    description="許可された署名付きURLから画像を取得してS3にアップロードし、URLを返します。セキュリティ上、事前に設定されたドメインのURLのみ受け付けます。",
    response_description="アップロードされた画像のURL",
    tags=["LGTM Images V2"],
    status_code=202,
    responses={
        202: {
            "description": "受理された（アップロード処理中）",
            "content": {
                "application/json": {
                    "example": {
                        "imageUrl": "https://lgtm-images.lgtmeow.com/2024/01/15/14/5947f291-a46e-453c-a230-0d756d7174cb.webp"
                    }
                }
            },
        },
        400: {
            "description": "無効なURLまたは許可されていないドメイン",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_url": {
                            "summary": "無効なURL",
                            "value": {"error": "Invalid URL provided"},
                        },
                        "domain_not_allowed": {
                            "summary": "許可されていないドメイン",
                            "value": {"error": "URL domain is not allowed"},
                        },
                        "url_not_accessible": {
                            "summary": "URLにアクセスできない",
                            "value": {"error": "URL not accessible"},
                        },
                    }
                }
            },
        },
        401: {
            "description": "認証エラー",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid authorization header"}
                }
            },
        },
        422: {
            "description": "画像取得失敗または無効な画像形式",
            "content": {
                "application/json": {
                    "examples": {
                        "fetch_failed": {
                            "summary": "画像取得失敗",
                            "value": {"error": "Failed to fetch image from URL"},
                        },
                        "invalid_format": {
                            "summary": "無効な画像形式",
                            "value": {
                                "error": "invalid image extension or unsupported format"
                            },
                        },
                    }
                }
            },
        },
        500: {
            "description": "サーバーエラー",
            "content": {
                "application/json": {"example": {"error": "Internal server error"}}
            },
        },
    },
)
async def create_lgtm_image_from_url(
    request_body: LgtmImageCreateFromUrlRequest,
    image_fetch_repository: Annotated[
        ImageFetchRepositoryInterface, Depends(create_image_fetch_repository)
    ],
    object_storage_repository: Annotated[
        ObjectStorageRepositoryInterface, Depends(create_object_storage_repository)
    ],
    base_url: str = Depends(get_lgtm_images_base_url),
    token_payload: dict[str, Any] = Depends(verify_token),
) -> JSONResponse:
    return await LgtmImageController.create_from_url(
        image_fetch_repository,
        object_storage_repository,
        base_url,
        request_body,
    )
