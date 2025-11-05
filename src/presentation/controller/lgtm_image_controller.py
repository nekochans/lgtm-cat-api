# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse

from domain.lgtm_image import LgtmImage
from domain.lgtm_image_errors import (
    ErrImageFetchFailed,
    ErrInvalidImageExtension,
    ErrInvalidUrl,
    ErrRecordCount,
    ErrUrlNotAccessible,
)
from domain.repository.lgtm_image_repository_interface import (
    LgtmImageRepositoryInterface,
)
from log.logger import get_logger
from presentation.controller.lgtm_image_request import (
    LgtmImageCreateFromUrlRequest,
    LgtmImageCreateRequest,
)
from presentation.controller.lgtm_image_response import (
    LgtmImageCreateResponse,
    LgtmImageItem,
    LgtmImageRandomListResponse,
    LgtmImageRecentlyCreatedListResponse,
)
from presentation.controller.response_helper import (
    create_json_response,
    create_error_response,
)
from usecase.create_lgtm_image_from_url_usecase import (
    CreateLgtmImageFromUrlUseCase,
)
from usecase.create_lgtm_image_usecase import CreateLgtmImageUsecase
from usecase.extract_random_lgtm_images_usecase import (
    ExtractRandomLgtmImagesUsecase,
)
from usecase.retrieve_recently_created_lgtm_images_usecase import (
    RetrieveRecentlyCreatedLgtmImagesUsecase,
)

if TYPE_CHECKING:
    from domain.repository.image_fetch_repository_interface import (
        ImageFetchRepositoryInterface,
    )
    from domain.repository.object_storage_repository_interface import (
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
            logger.error(f"Error creating LGTM image: {e}")
            return create_error_response(e)

    @staticmethod
    async def create_from_url(
        image_fetch_repository: "ImageFetchRepositoryInterface",
        object_storage_repository: "ObjectStorageRepositoryInterface",
        base_url: str,
        request_body: LgtmImageCreateFromUrlRequest,
    ) -> JSONResponse:
        logger.info(
            "Creating LGTM image from URL",
            extra={"image_url": request_body.image_url},
        )

        try:
            uploaded_image = await CreateLgtmImageFromUrlUseCase.execute(
                image_fetch_repository=image_fetch_repository,
                object_storage_repository=object_storage_repository,
                base_url=base_url,
                image_url=request_body.image_url,
            )
            response = LgtmImageCreateResponse(imageUrl=uploaded_image["url"])  # type: ignore[arg-type]
            return create_json_response(response, status_code=202)
        except ErrInvalidUrl as e:
            logger.error(f"Invalid URL provided: {e}")
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid URL provided"},
            )
        except ErrUrlNotAccessible as e:
            logger.error(f"URL not accessible: {e}")
            return JSONResponse(
                status_code=400,
                content={"error": "URL not accessible"},
            )
        except ErrImageFetchFailed as e:
            logger.error(f"Failed to fetch image: {e}")
            return JSONResponse(
                status_code=422,
                content={"error": "Failed to fetch image from URL"},
            )
        except ErrInvalidImageExtension as e:
            logger.error(f"Invalid image extension: {e}")
            return JSONResponse(
                status_code=422,
                content={"error": "Invalid image extension or unsupported format"},
            )
        except Exception as e:
            logger.error(f"Error creating LGTM image from URL: {e}")
            return create_error_response(e)

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
            logger.error(f"Error extracting random LGTM images: {e}")
            return create_error_response(e)

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
            logger.error(f"Error retrieving recently created LGTM images: {e}")
            return create_error_response(e)
