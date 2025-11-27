# 絶対厳守：編集前に必ずAI実装ルールを読む
"""猫画像判定エンドポイントのルーター定義"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from config import (
    get_aws_rekognition_region,
    get_image_allowed_domain,
    get_image_fetch_timeout,
    get_max_image_size,
)
from domain.cat_image_validation_policy import (
    CatImageValidationPolicy,
    DEFAULT_VALIDATION_POLICY,
)
from domain.image_analysis_interface import ImageAnalysisServiceInterface
from domain.repository.image_fetch_repository_interface import (
    ImageFetchRepositoryInterface,
)
from infrastructure.rekognition_image_analysis_service import (
    RekognitionImageAnalysisService,
)
from infrastructure.repository.http_image_fetch_repository import (
    HttpImageFetchRepository,
)
from presentation.controller.cat_image_controller import CatImageController
from presentation.controller.cat_image_request import (
    CatImageValidationFromS3Request,
    CatImageValidationFromUrlRequest,
)
from presentation.controller.cat_image_response import CatImageValidationResponse
from presentation.dependencies.auth import verify_token

router = APIRouter()


def create_image_analysis_service(
    region: Annotated[str, Depends(get_aws_rekognition_region)],
) -> ImageAnalysisServiceInterface:
    """ImageAnalysisServiceInterfaceインスタンスを生成"""
    return RekognitionImageAnalysisService(region=region)


def get_validation_policy() -> CatImageValidationPolicy:
    """猫画像判定ポリシーを取得"""
    return DEFAULT_VALIDATION_POLICY


def create_image_fetch_repository(
    timeout: Annotated[int, Depends(get_image_fetch_timeout)],
    max_size: Annotated[int, Depends(get_max_image_size)],
    allowed_domain: Annotated[str, Depends(get_image_allowed_domain)],
) -> ImageFetchRepositoryInterface:
    """ImageFetchRepositoryInterfaceインスタンスを生成"""
    return HttpImageFetchRepository(
        timeout=timeout, max_size=max_size, allowed_domain=allowed_domain
    )


@router.post(
    "/cat-images/validate/url",
    summary="URLからの猫画像判定",
    description="署名付きURLから画像を取得し、LGTM画像として適切な猫画像かを判定します。不適切なコンテンツ、人の顔、猫以外の画像を検出します。",
    response_description="猫画像判定結果",
    response_model=CatImageValidationResponse,
    tags=["Cat Images"],
    responses={
        200: {
            "description": "判定成功",
            "content": {
                "application/json": {
                    "examples": {
                        "acceptable": {
                            "summary": "受け入れ可能な猫画像",
                            "value": {"isAcceptableCatImage": True},
                        },
                        "not_acceptable": {
                            "summary": "受け入れ不可の画像",
                            "value": {
                                "isAcceptableCatImage": False,
                                "notAcceptableReason": "not cat image",
                            },
                        },
                    }
                }
            },
        },
        400: {
            "description": "無効なURL、またはアクセスできないURL",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_url": {
                            "summary": "無効なURL",
                            "value": {"error": "Invalid URL provided"},
                        },
                        "url_not_accessible": {
                            "summary": "アクセスできないURL",
                            "value": {"error": "URL not accessible"},
                        },
                    }
                }
            },
        },
        422: {
            "description": "画像取得失敗、または無効な画像形式",
            "content": {
                "application/json": {
                    "examples": {
                        "fetch_failed": {
                            "summary": "画像取得失敗",
                            "value": {"error": "Failed to fetch image from URL"},
                        },
                        "invalid_extension": {
                            "summary": "無効な画像形式",
                            "value": {
                                "error": "Invalid image extension or unsupported format"
                            },
                        },
                    }
                }
            },
        },
        500: {
            "description": "サーバーエラー（画像解析失敗、予期しないエラー）",
            "content": {
                "application/json": {"example": {"error": "Internal server error"}}
            },
        },
    },
)
async def validate_cat_image_from_url(
    request_body: CatImageValidationFromUrlRequest,
    image_analysis_service: Annotated[
        ImageAnalysisServiceInterface, Depends(create_image_analysis_service)
    ],
    image_fetch_repository: Annotated[
        ImageFetchRepositoryInterface, Depends(create_image_fetch_repository)
    ],
    policy: Annotated[CatImageValidationPolicy, Depends(get_validation_policy)],
    token_payload: Annotated[dict[str, Any], Depends(verify_token)],
) -> JSONResponse:
    return await CatImageController.validate_from_url(
        request_body,
        image_analysis_service,
        image_fetch_repository,
        policy,
    )


@router.post(
    "/cat-images/validate/s3",
    summary="S3オブジェクト参照での猫画像判定",
    description="S3バケットとオブジェクトキーを指定し、LGTM画像として適切な猫画像かを判定します。不適切なコンテンツ、人の顔、猫以外の画像を検出します。",
    response_description="猫画像判定結果",
    response_model=CatImageValidationResponse,
    tags=["Cat Images"],
    responses={
        200: {
            "description": "判定成功",
            "content": {
                "application/json": {
                    "examples": {
                        "acceptable": {
                            "summary": "受け入れ可能な猫画像",
                            "value": {"isAcceptableCatImage": True},
                        },
                        "not_acceptable": {
                            "summary": "受け入れ不可の画像",
                            "value": {
                                "isAcceptableCatImage": False,
                                "notAcceptableReason": "not cat image",
                            },
                        },
                    }
                }
            },
        },
        500: {
            "description": "サーバーエラー（S3アクセスエラー、画像解析失敗、予期しないエラー）",
            "content": {
                "application/json": {"example": {"error": "Internal server error"}}
            },
        },
    },
)
async def validate_cat_image_from_s3(
    request_body: CatImageValidationFromS3Request,
    image_analysis_service: Annotated[
        ImageAnalysisServiceInterface, Depends(create_image_analysis_service)
    ],
    policy: Annotated[CatImageValidationPolicy, Depends(get_validation_policy)],
    token_payload: Annotated[dict[str, Any], Depends(verify_token)],
) -> JSONResponse:
    return await CatImageController.validate_from_s3(
        request_body,
        image_analysis_service,
        policy,
    )
