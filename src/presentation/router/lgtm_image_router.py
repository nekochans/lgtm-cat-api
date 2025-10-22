# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_lgtm_images_base_url, get_upload_s3_bucket_name
from src.domain.repository.lgtm_image_repository_interface import (
    LgtmImageRepositoryInterface,
)
from src.infrastructure.database import create_db_session
from src.infrastructure.lgtm_image_repository import LgtmImageRepository
from src.domain.repository.object_storage_repository_interface import (
    ObjectStorageRepositoryInterface,
)
from src.domain.repository.unique_id_generator_interface import (
    UniqueIdGeneratorInterface,
)
from src.infrastructure.s3_repository import S3Repository
from src.infrastructure.uuid_generator import UuidGenerator
from src.presentation.controller.lgtm_image_controller import LgtmImageController
from src.presentation.controller.lgtm_image_request import LgtmImageCreateRequest

router = APIRouter()


def create_lgtm_image_repository(
    session: Annotated[AsyncSession, Depends(create_db_session)],
) -> LgtmImageRepositoryInterface:
    return LgtmImageRepository(session)


def create_object_storage_repository(
    bucket_name: str = Depends(get_upload_s3_bucket_name),
) -> ObjectStorageRepositoryInterface:
    return S3Repository(bucket_name)


def create_id_generator() -> UniqueIdGeneratorInterface:
    return UuidGenerator()


@router.post(
    "/lgtm-images",
    summary="LGTM画像を作成",
    description="base64エンコードされた画像をS3にアップロードし、URLを返します。",
    response_description="アップロードされた画像のURL",
    tags=["LGTM Images"],
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
        422: {
            "description": "無効な画像拡張子",
            "content": {
                "application/json": {
                    "example": {"error": "Invalid image extension: .gif"}
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
async def create_lgtm_image(
    request_body: LgtmImageCreateRequest,
    object_storage_repository: Annotated[
        ObjectStorageRepositoryInterface, Depends(create_object_storage_repository)
    ],
    id_generator: Annotated[UniqueIdGeneratorInterface, Depends(create_id_generator)],
    base_url: str = Depends(get_lgtm_images_base_url),
) -> JSONResponse:
    return await LgtmImageController.create(
        object_storage_repository, id_generator, base_url, request_body
    )


@router.get(
    "/lgtm-images",
    summary="ランダムなLGTM画像を取得",
    description="ランダムに選択されたLGTM画像のリストを返します。",
    response_description="ランダムに選択されたLGTM画像のリスト",
    tags=["LGTM Images"],
    responses={
        200: {
            "description": "成功時のレスポンス",
            "content": {
                "application/json": {
                    "example": {
                        "lgtmImages": [
                            {
                                "id": "1",
                                "url": "https://example.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp",
                            },
                            {
                                "id": "2",
                                "url": "https://example.com/2021/03/16/23/6947f291-a46e-453c-a230-0d756d7174cb.webp",
                            },
                        ]
                    }
                }
            },
        }
    },
)
async def extract_random_lgtm_images(
    repository: Annotated[
        LgtmImageRepositoryInterface, Depends(create_lgtm_image_repository)
    ],
    base_url: str = Depends(get_lgtm_images_base_url),
) -> JSONResponse:
    return await LgtmImageController.exec(repository, base_url)


@router.get(
    "/lgtm-images/recently-created",
    summary="最近作成されたLGTM画像を取得",
    description="最近作成されたLGTM画像のリストを返します。",
    response_description="最近作成されたLGTM画像のリスト",
    tags=["LGTM Images"],
    responses={
        200: {
            "description": "成功時のレスポンス",
            "content": {
                "application/json": {
                    "example": {
                        "lgtmImages": [
                            {
                                "id": "1",
                                "url": "https://example.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp",
                            },
                            {
                                "id": "2",
                                "url": "https://example.com/2021/03/16/23/6947f291-a46e-453c-a230-0d756d7174cb.webp",
                            },
                        ]
                    }
                }
            },
        }
    },
)
async def retrieve_recently_created_lgtm_images(
    repository: Annotated[
        LgtmImageRepositoryInterface, Depends(create_lgtm_image_repository)
    ],
    base_url: str = Depends(get_lgtm_images_base_url),
) -> JSONResponse:
    return await LgtmImageController.exec_recently_created(repository, base_url)
