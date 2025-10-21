# 絶対厳守：編集前に必ずAI実装ルールを読む

from fastapi.responses import JSONResponse

from src.domain.lgtm_image import LgtmImage
from src.domain.lgtm_image_errors import ErrRecordCount
from src.domain.repository.lgtm_image_repository_interface import (
    LgtmImageRepositoryInterface,
)
from src.log.logger import get_logger
from src.presentation.controller.lgtm_image_response import (
    LgtmImageItem,
    LgtmImageRandomListResponse,
    LgtmImageRecentlyCreatedListResponse,
)
from src.presentation.controller.response_helper import create_json_response
from src.usecase.extract_random_lgtm_images_usecase import (
    ExtractRandomLgtmImagesUsecase,
)
from src.usecase.retrieve_recently_created_lgtm_images_usecase import (
    RetrieveRecentlyCreatedLgtmImagesUsecase,
)

logger = get_logger(__name__)


class LgtmImageController:
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
            response = LgtmImageRandomListResponse(LgtmImages=image_items)
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
            response = LgtmImageRecentlyCreatedListResponse(LgtmImages=image_items)
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
