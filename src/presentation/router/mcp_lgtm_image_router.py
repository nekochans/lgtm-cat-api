# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from presentation.controller.lgtm_image_response import (
    LgtmImageRandomListResponse,
    LgtmImageRecentlyCreatedListResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_lgtm_images_base_url
from domain.repository.lgtm_image_repository_interface import (
    LgtmImageRepositoryInterface,
)
from infrastructure.database import create_db_session
from infrastructure.lgtm_image_repository import LgtmImageRepository
from presentation.controller.lgtm_image_controller import LgtmImageController

router = APIRouter(prefix="/mcp")


def create_lgtm_image_repository(
    session: Annotated[AsyncSession, Depends(create_db_session)],
) -> LgtmImageRepositoryInterface:
    return LgtmImageRepository(session)


@router.get(
    "/lgtm-images",
    summary="ランダムなLGTM画像を取得（MCP用）",
    description="ランダムに選択されたLGTM画像のリストを返します。認証不要。",
    response_description="ランダムに選択されたLGTM画像のリスト",
    response_model=LgtmImageRandomListResponse,
    tags=["mcp_tool"],
    operation_id="get_random_lgtm_images",
    responses={
        200: {
            "description": "成功時のレスポンス",
            "content": {
                "application/json": {
                    "example": {
                        "lgtmImages": [
                            {
                                "id": "1",
                                "url": "https://lgtm-images.lgtmeow.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp",
                            },
                            {
                                "id": "2",
                                "url": "https://lgtm-images.lgtmeow.com/2021/03/16/23/6947f291-a46e-453c-a230-0d756d7174cb.webp",
                            },
                        ]
                    }
                }
            },
        },
        404: {
            "description": "LGTM画像が見つからない",
            "content": {
                "application/json": {
                    "example": {"error": "Insufficient LGTM images available"}
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
async def extract_random_lgtm_images(
    repository: Annotated[
        LgtmImageRepositoryInterface, Depends(create_lgtm_image_repository)
    ],
    base_url: Annotated[str, Depends(get_lgtm_images_base_url)],
) -> JSONResponse:
    return await LgtmImageController.exec(repository, base_url)


@router.get(
    "/lgtm-images/recently-created",
    summary="最近作成されたLGTM画像を取得（MCP用）",
    description="最近作成されたLGTM画像のリストを返します。認証不要。",
    response_description="最近作成されたLGTM画像のリスト",
    response_model=LgtmImageRecentlyCreatedListResponse,
    tags=["mcp_tool"],
    operation_id="get_recently_created_lgtm_images",
    responses={
        200: {
            "description": "成功時のレスポンス",
            "content": {
                "application/json": {
                    "example": {
                        "lgtmImages": [
                            {
                                "id": "1",
                                "url": "https://lgtm-images.lgtmeow.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp",
                            },
                            {
                                "id": "2",
                                "url": "https://lgtm-images.lgtmeow.com/2021/03/16/23/6947f291-a46e-453c-a230-0d756d7174cb.webp",
                            },
                        ]
                    }
                }
            },
        },
        404: {
            "description": "LGTM画像が見つからない",
            "content": {
                "application/json": {
                    "example": {"error": "Insufficient LGTM images available"}
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
async def retrieve_recently_created_lgtm_images(
    repository: Annotated[
        LgtmImageRepositoryInterface, Depends(create_lgtm_image_repository)
    ],
    base_url: Annotated[str, Depends(get_lgtm_images_base_url)],
) -> JSONResponse:
    return await LgtmImageController.exec_recently_created(repository, base_url)
