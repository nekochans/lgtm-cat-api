# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from presentation.controller.lgtm_image_response import (
    LgtmImageRandomListResponse,
    LgtmImageRecentlyCreatedListResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_lgtm_images_base_url, get_lgtmeow_url
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
    summary="Get random LGTM images",
    description="Returns a list of randomly selected LGTM (Looks Good To Me) cat images for use in code review comments and pull request approvals.",
    response_description="A list of randomly selected LGTM images",
    response_model=LgtmImageRandomListResponse,
    tags=["mcp_tool"],
    operation_id="get_random_lgtm_images",
    responses={
        200: {
            "description": "Success Response",
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
            "description": "No LGTM images found",
            "content": {
                "application/json": {
                    "example": {"error": "Insufficient LGTM images available"}
                }
            },
        },
        500: {
            "description": "Internal server error",
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
    summary="Get recently created LGTM images",
    description="Returns a list of the most recently created LGTM (Looks Good To Me) cat images for use in code review comments and pull request approvals.",
    response_description="A list of recently created LGTM images",
    response_model=LgtmImageRecentlyCreatedListResponse,
    tags=["mcp_tool"],
    operation_id="get_recently_created_lgtm_images",
    responses={
        200: {
            "description": "Success Response",
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
            "description": "No LGTM images found",
            "content": {
                "application/json": {
                    "example": {"error": "Insufficient LGTM images available"}
                }
            },
        },
        500: {
            "description": "Internal server error",
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


@router.get(
    "/lgtm-images/markdown",
    summary="Get a random LGTM image in markdown format",
    description="Returns a single randomly selected LGTM (Looks Good To Me) cat image in markdown format for use in code review comments and pull request approvals.",
    response_description="Markdown formatted LGTM image",
    response_class=PlainTextResponse,
    response_model=None,
    tags=["mcp_tool"],
    operation_id="get_random_lgtm_markdown",
    responses={
        200: {
            "description": "Success Response - Markdown formatted LGTM image",
            "content": {
                "text/plain": {
                    "example": "[![LGTMeow](https://lgtm-images.lgtmeow.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp)](https://lgtmeow.com)"
                }
            },
        },
        404: {
            "description": "No LGTM images found",
            "content": {
                "application/json": {
                    "example": {"error": "Insufficient LGTM images available"}
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {"example": {"error": "Internal server error"}}
            },
        },
    },
)
async def get_random_lgtm_markdown(
    repository: Annotated[
        LgtmImageRepositoryInterface, Depends(create_lgtm_image_repository)
    ],
    base_url: Annotated[str, Depends(get_lgtm_images_base_url)],
    lgtmeow_url: Annotated[str, Depends(get_lgtmeow_url)],
) -> PlainTextResponse | JSONResponse:
    return await LgtmImageController.exec_random_markdown(
        repository, base_url, lgtmeow_url
    )
