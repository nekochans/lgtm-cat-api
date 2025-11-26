# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import TYPE_CHECKING

from domain.repository.lgtm_image_search_repository_interface import (
    LgtmImageSearchRepositoryInterface,
)
from fastapi.responses import JSONResponse

from domain.lgtm_image import LgtmImage
from domain.lgtm_image_errors import (
    ErrImageFetchFailed,
    ErrInvalidImageExtension,
    ErrInvalidSearchQuery,
    ErrInvalidUrl,
    ErrRecordCount,
    ErrRekognitionFailed,
    ErrUrlNotAccessible,
)
from domain.repository.lgtm_image_repository_interface import (
    LgtmImageRepositoryInterface,
)
from log.logger import get_logger
from log.url_sanitizer import sanitize_url_for_logging
from presentation.controller.lgtm_image_request import (
    CatImageValidationRequest,
    LgtmImageCreateFromUrlRequest,
    LgtmImageCreateRequest,
    LgtmImageSearchByImageFromUrlRequest,
    LgtmImageSearchByImageRequest,
)
from presentation.controller.lgtm_image_response import (
    CatImageValidationResponse,
    LgtmImageCreateResponse,
    LgtmImageItem,
    LgtmImageRandomListResponse,
    LgtmImageRecentlyCreatedListResponse,
    LgtmImageSearchByImageResponse,
    LgtmImageSearchItem,
    LgtmImageSearchResponse,
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
from usecase.search_lgtm_images_by_image import SearchLgtmImagesByImageUsecase
from usecase.search_lgtm_images_by_image_from_url_usecase import (
    SearchLgtmImagesByImageFromUrlUsecase,
)
from usecase.search_lgtm_images_by_text import SearchLgtmImagesByTextUsecase
from usecase.validate_cat_image_usecase import ValidateCatImageUseCase

if TYPE_CHECKING:
    from domain.cat_image_validation_policy import CatImageValidationPolicy
    from domain.image_analysis_interface import ImageAnalysisServiceInterface
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
            response = LgtmImageCreateResponse(image_url=uploaded_image["url"])  # type: ignore[arg-type]
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
        sanitized_url = sanitize_url_for_logging(request_body.image_url)
        logger.info(
            "Creating LGTM image from URL",
            extra={"image_url": sanitized_url},
        )

        try:
            uploaded_image = await CreateLgtmImageFromUrlUseCase.execute(
                image_fetch_repository=image_fetch_repository,
                object_storage_repository=object_storage_repository,
                base_url=base_url,
                image_url=request_body.image_url,
            )
            response = LgtmImageCreateResponse(image_url=uploaded_image["url"])  # type: ignore[arg-type]
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
            response = LgtmImageRandomListResponse(lgtm_images=image_items)
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
            response = LgtmImageRecentlyCreatedListResponse(lgtm_images=image_items)
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

    @staticmethod
    async def search_by_text(
        repository: LgtmImageSearchRepositoryInterface,
        query: str,
    ) -> JSONResponse:
        logger.info("Searching LGTM images by text", extra={"query_length": len(query)})

        try:
            results = await SearchLgtmImagesByTextUsecase.execute(repository, query)

            # ドメインエンティティをレスポンスモデルに変換（順序を保持）
            image_items = [
                LgtmImageSearchItem(
                    id=result["id"],
                    url=result["url"],  # type: ignore[arg-type]
                    similarity_score=result["similarity_score"],
                )
                for result in results
            ]

            response = LgtmImageSearchResponse(lgtm_images=image_items)
            return create_json_response(response)

        except ErrInvalidSearchQuery as e:
            # 空クエリなどのバリデーションエラー
            logger.error(f"Validation error: {e}")
            return JSONResponse(status_code=400, content={"error": str(e)})
        except Exception as e:
            # その他の予期しないエラー
            logger.error(f"Error searching LGTM images by text: {e}")
            return create_error_response(e)

    @staticmethod
    async def search_by_image(
        repository: LgtmImageSearchRepositoryInterface,
        request: LgtmImageSearchByImageRequest,
    ) -> JSONResponse:
        logger.info(
            "Searching LGTM images by image",
            extra={"image_extension": request.image_extension},
        )

        try:
            # ユースケース実行
            similar_images = await SearchLgtmImagesByImageUsecase.execute(
                repository, request.image, request.image_extension
            )

            # レスポンスモデルに変換
            image_items = [
                LgtmImageSearchItem(
                    id=img["id"],
                    url=img["url"],  # type: ignore[arg-type]
                    similarity_score=img["similarity_score"],
                )
                for img in similar_images
            ]
            response = LgtmImageSearchByImageResponse(lgtm_images=image_items)

            # JSONResponse返却
            return create_json_response(response)

        except Exception as e:
            # エラーハンドリング
            logger.error(f"Error searching LGTM images by image: {e}")
            return create_error_response(e)

    @staticmethod
    async def search_by_image_from_url(
        image_fetch_repository: "ImageFetchRepositoryInterface",
        repository: LgtmImageSearchRepositoryInterface,
        request: LgtmImageSearchByImageFromUrlRequest,
    ) -> JSONResponse:
        sanitized_url = sanitize_url_for_logging(request.image_url)
        logger.info(
            "Searching LGTM images by image from URL",
            extra={"image_url": sanitized_url},
        )

        try:
            # ユースケース実行
            similar_images = await SearchLgtmImagesByImageFromUrlUsecase.execute(
                image_fetch_repository=image_fetch_repository,
                search_repository=repository,
                image_url=request.image_url,
            )

            # レスポンスモデルに変換
            image_items = [
                LgtmImageSearchItem(
                    id=img["id"],
                    url=img["url"],  # type: ignore[arg-type]
                    similarity_score=img["similarity_score"],
                )
                for img in similar_images
            ]
            response = LgtmImageSearchByImageResponse(lgtm_images=image_items)

            # JSONResponse返却
            return create_json_response(response)

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
            logger.error(f"Error searching LGTM images by image from URL: {e}")
            return create_error_response(e)

    @staticmethod
    async def validate_cat_image(
        request: CatImageValidationRequest,
        image_analysis_service: "ImageAnalysisServiceInterface",
        image_fetch_repository: "ImageFetchRepositoryInterface",
        policy: "CatImageValidationPolicy",
    ) -> JSONResponse:
        sanitized_url = sanitize_url_for_logging(request.image_url)
        logger.info(
            "Validating cat image",
            extra={"image_url": sanitized_url},
        )

        try:
            usecase = ValidateCatImageUseCase(
                image_analysis_service, image_fetch_repository, policy
            )
            result = await usecase.execute(request.image_url)

            response = CatImageValidationResponse(
                isAcceptableCatImage=result["is_acceptable"],
                notAcceptableReason=result.get("reason"),
            )

            return create_json_response(response)

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
        except ErrRekognitionFailed as e:
            logger.error(f"Rekognition API error: {e}")
            return JSONResponse(
                status_code=500, content={"error": "Image validation failed"}
            )
        except Exception as e:
            logger.error(f"Unexpected error in validate_cat_image: {e}")
            return JSONResponse(status_code=500, content={"error": str(e)})
