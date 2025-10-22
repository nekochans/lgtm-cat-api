# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_lgtm_images_base_url
from src.domain.repository.lgtm_image_repository_interface import (
    LgtmImageRepositoryInterface,
)
from src.infrastructure.database import create_db_session
from src.infrastructure.lgtm_image_repository import LgtmImageRepository
from src.presentation.controller.lgtm_image_controller import LgtmImageController

router = APIRouter()


def create_lgtm_image_repository(
    session: Annotated[AsyncSession, Depends(create_db_session)],
) -> LgtmImageRepositoryInterface:
    return LgtmImageRepository(session)


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
