# 絶対厳守：編集前に必ずAI実装ルールを読む
"""猫画像判定コントローラー"""

from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse

from domain.lgtm_image_errors import (
    ErrImageFetchFailed,
    ErrInvalidImageExtension,
    ErrInvalidUrl,
    ErrRekognitionFailed,
    ErrUrlNotAccessible,
)
from log.logger import get_logger
from log.url_sanitizer import sanitize_url_for_logging
from presentation.controller.cat_image_request import (
    CatImageValidationFromS3Request,
    CatImageValidationFromUrlRequest,
)
from presentation.controller.cat_image_response import CatImageValidationResponse
from presentation.controller.response_helper import (
    create_error_response,
    create_json_response,
)
from usecase.validate_cat_image_from_s3_usecase import ValidateCatImageFromS3UseCase
from usecase.validate_cat_image_usecase import ValidateCatImageUseCase

if TYPE_CHECKING:
    from domain.cat_image_validation_policy import CatImageValidationPolicy
    from domain.image_analysis_interface import ImageAnalysisServiceInterface
    from domain.repository.image_fetch_repository_interface import (
        ImageFetchRepositoryInterface,
    )

logger = get_logger(__name__)


class CatImageController:
    """猫画像判定のコントローラー"""

    @staticmethod
    async def validate_from_url(
        request: CatImageValidationFromUrlRequest,
        image_analysis_service: "ImageAnalysisServiceInterface",
        image_fetch_repository: "ImageFetchRepositoryInterface",
        policy: "CatImageValidationPolicy",
    ) -> JSONResponse:
        """URLからの猫画像判定"""
        sanitized_url = sanitize_url_for_logging(request.image_url)
        logger.info(
            "Validating cat image from URL",
            extra={"image_url": sanitized_url},
        )

        try:
            usecase = ValidateCatImageUseCase(
                image_analysis_service, image_fetch_repository, policy
            )
            result = await usecase.execute(request.image_url)

            response = CatImageValidationResponse(
                is_acceptable_cat_image=result["is_acceptable"],
                not_acceptable_reason=result.get("reason"),
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
            return create_error_response(e)
        except Exception as e:
            logger.error(f"Unexpected error in validate_from_url: {e}")
            return create_error_response(e)

    @staticmethod
    async def validate_from_s3(
        request: CatImageValidationFromS3Request,
        image_analysis_service: "ImageAnalysisServiceInterface",
        policy: "CatImageValidationPolicy",
    ) -> JSONResponse:
        """S3オブジェクト参照での猫画像判定"""
        logger.info(
            "Validating cat image from S3",
            extra={"bucket": request.bucket_name, "key": request.object_key},
        )

        try:
            usecase = ValidateCatImageFromS3UseCase(image_analysis_service, policy)
            result = await usecase.execute(request.bucket_name, request.object_key)

            response = CatImageValidationResponse(
                is_acceptable_cat_image=result["is_acceptable"],
                not_acceptable_reason=result.get("reason"),
            )

            return create_json_response(response)

        except ErrRekognitionFailed as e:
            logger.error(f"Rekognition API error: {e}")
            return create_error_response(e)
        except Exception as e:
            logger.error(f"Unexpected error in validate_from_s3: {e}")
            return create_error_response(e)
