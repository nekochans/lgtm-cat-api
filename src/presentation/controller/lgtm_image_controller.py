# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse

from src.domain.lgtm_image import LgtmImage
from src.domain.lgtm_image_errors import ErrInvalidImageExtension, ErrRecordCount
from src.domain.repository.lgtm_image_repository_interface import (
    LgtmImageRepositoryInterface,
)
from src.log.logger import get_logger
from src.presentation.controller.lgtm_image_request import LgtmImageCreateRequest
from src.presentation.controller.lgtm_image_response import (
    LgtmImageCreateResponse,
    LgtmImageItem,
    LgtmImageRandomListResponse,
    LgtmImageRecentlyCreatedListResponse,
)
from src.presentation.controller.response_helper import create_json_response
from src.usecase.create_lgtm_image_usecase import CreateLgtmImageUsecase
from src.usecase.extract_random_lgtm_images_usecase import (
    ExtractRandomLgtmImagesUsecase,
)
from src.usecase.retrieve_recently_created_lgtm_images_usecase import (
    RetrieveRecentlyCreatedLgtmImagesUsecase,
)

if TYPE_CHECKING:
    from src.domain.repository.object_storage_repository_interface import (
        ObjectStorageRepositoryInterface,
    )

logger = get_logger(__name__)


class LgtmImageController:
    @staticmethod
    async def create(
        object_storage_repository: "ObjectStorageRepositoryInterface",
        base_url: str,
        request_body: LgtmImageCreateRequest,
    ) -> JSONResponse:
        logger.info("Creating new LGTM image")

        try:
            uploaded_image = await CreateLgtmImageUsecase.execute(
                object_storage_repository=object_storage_repository,
                base_url=base_url,
                image=request_body.image,
                image_extension=request_body.image_extension,
            )
            response = LgtmImageCreateResponse(imageUrl=uploaded_image["url"])  # type: ignore[arg-type]
            return create_json_response(response, status_code=202)
        except ErrInvalidImageExtension as e:
            logger.error(f"Invalid image extension: {e}")
            return JSONResponse(
                status_code=422,
                content={"error": "Invalid image extension provided"},
            )
        except Exception as e:
            logger.error(
                "Unexpected error occurred",
                exc_info=True,
                extra={"error_type": type(e).__name__, "error_message": str(e)},
            )
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error occurred"},
            )

    @staticmethod
    async def exec(
        repository: LgtmImageRepositoryInterface,
        base_url: str,
    ) -> JSONResponse:
        logger.info("Extracting random LGTM images")

        try:
            images: list[LgtmImage] = await ExtractRandomLgtmImagesUsecase.execute(
                repository, base_url
            )
            image_items = [
                LgtmImageItem(id=image["id"], url=image["url"])  # type: ignore[arg-type]
                for image in images
            ]
            response = LgtmImageRandomListResponse(lgtmImages=image_items)
            return create_json_response(response)
        except ErrRecordCount:
            logger.error("Insufficient LGTM images available")
            return JSONResponse(
                status_code=404,
                content={"error": "Insufficient LGTM images available"},
            )
        except Exception as e:
            logger.error(
                "Unexpected error occurred",
                exc_info=True,
                extra={"error_type": type(e).__name__, "error_message": str(e)},
            )
            return JSONResponse(
                status_code=500,
                content={"error": f"Internal server error: {str(e)}"},
            )

    @staticmethod
    async def exec_recently_created(
        repository: LgtmImageRepositoryInterface,
        base_url: str,
    ) -> JSONResponse:
        logger.info("Retrieving recently created LGTM images")

        try:
            images: list[
                LgtmImage
            ] = await RetrieveRecentlyCreatedLgtmImagesUsecase.execute(
                repository, base_url
            )
            image_items = [
                LgtmImageItem(id=image["id"], url=image["url"])  # type: ignore[arg-type]
                for image in images
            ]
            response = LgtmImageRecentlyCreatedListResponse(lgtmImages=image_items)
            return create_json_response(response)
        except ErrRecordCount:
            logger.error("Insufficient LGTM images available")
            return JSONResponse(
                status_code=404,
                content={"error": "Insufficient LGTM images available"},
            )
        except Exception as e:
            logger.error(
                "Unexpected error occurred",
                exc_info=True,
                extra={"error_type": type(e).__name__, "error_message": str(e)},
            )
            return JSONResponse(
                status_code=500,
                content={"error": f"Internal server error: {str(e)}"},
            )
