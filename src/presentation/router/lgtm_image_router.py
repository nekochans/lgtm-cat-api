# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from presentation.controller.lgtm_image_response import (
    CatImageValidationResponse,
    LgtmImageCreateResponse,
    LgtmImageRandomListResponse,
    LgtmImageRecentlyCreatedListResponse,
    LgtmImageSearchByImageResponse,
    LgtmImageSearchResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession

from config import (
    get_aws_bedrock_embedding_model_id,
    get_aws_bedrock_region,
    get_aws_rekognition_region,
    get_image_allowed_domain,
    get_image_fetch_timeout,
    get_lgtm_images_base_url,
    get_max_image_size,
    get_s3_vector_bucket_name,
    get_s3_vector_index_name,
    get_s3_vector_region,
    get_upload_s3_bucket_name,
)
from domain.repository.image_fetch_repository_interface import (
    ImageFetchRepositoryInterface,
)
from domain.repository.lgtm_image_repository_interface import (
    LgtmImageRepositoryInterface,
)
from domain.repository.lgtm_image_search_repository_interface import (
    LgtmImageSearchRepositoryInterface,
)
from domain.repository.object_storage_repository_interface import (
    ObjectStorageRepositoryInterface,
)
from domain.cat_image_validation_policy import (
    CatImageValidationPolicy,
    DEFAULT_VALIDATION_POLICY,
)
from infrastructure.bedrock_client import BedrockClient
from infrastructure.database import create_db_session
from infrastructure.lgtm_image_repository import LgtmImageRepository
from infrastructure.lgtm_image_search_repository import LgtmImageSearchRepository
from infrastructure.rekognition_image_analysis_service import (
    RekognitionImageAnalysisService,
)
from infrastructure.repository.http_image_fetch_repository import (
    HttpImageFetchRepository,
)
from infrastructure.s3_repository import S3Repository
from infrastructure.s3_vector_client import S3VectorClient
from presentation.controller.lgtm_image_controller import LgtmImageController
from presentation.controller.lgtm_image_request import (
    CatImageValidationRequest,
    LgtmImageCreateRequest,
    LgtmImageSearchByImageFromUrlRequest,
    LgtmImageSearchByImageRequest,
    TextSearchRequest,
)
from presentation.dependencies.auth import verify_token

router = APIRouter()


def create_lgtm_image_repository(
    session: Annotated[AsyncSession, Depends(create_db_session)],
) -> LgtmImageRepositoryInterface:
    return LgtmImageRepository(session)


def create_object_storage_repository(
    bucket_name: Annotated[str, Depends(get_upload_s3_bucket_name)],
) -> ObjectStorageRepositoryInterface:
    return S3Repository(bucket_name)


def create_lgtm_image_search_repository(
    base_url: Annotated[str, Depends(get_lgtm_images_base_url)],
    bedrock_region: Annotated[str, Depends(get_aws_bedrock_region)],
    bedrock_model_id: Annotated[str, Depends(get_aws_bedrock_embedding_model_id)],
    s3_vector_region: Annotated[str, Depends(get_s3_vector_region)],
    s3_vector_bucket_name: Annotated[str, Depends(get_s3_vector_bucket_name)],
    s3_vector_index_name: Annotated[str, Depends(get_s3_vector_index_name)],
) -> LgtmImageSearchRepositoryInterface:
    """LGTM画像検索リポジトリのインスタンスを生成"""
    bedrock_client = BedrockClient(
        region=bedrock_region,
        model_id=bedrock_model_id,
    )
    s3_vector_client = S3VectorClient(
        region=s3_vector_region,
        bucket_name=s3_vector_bucket_name,
        index_name=s3_vector_index_name,
    )
    return LgtmImageSearchRepository(bedrock_client, s3_vector_client, base_url)


def create_image_fetch_repository(
    timeout: Annotated[int, Depends(get_image_fetch_timeout)],
    max_size: Annotated[int, Depends(get_max_image_size)],
    allowed_domain: Annotated[str, Depends(get_image_allowed_domain)],
) -> ImageFetchRepositoryInterface:
    """画像取得リポジトリのインスタンスを生成"""
    return HttpImageFetchRepository(
        timeout=timeout, max_size=max_size, allowed_domain=allowed_domain
    )


def create_image_analysis_service(
    region: Annotated[str, Depends(get_aws_rekognition_region)],
) -> RekognitionImageAnalysisService:
    """RekognitionImageAnalysisServiceインスタンスを生成"""
    return RekognitionImageAnalysisService(region=region)


def get_validation_policy() -> CatImageValidationPolicy:
    """猫画像判定ポリシーを取得"""
    return DEFAULT_VALIDATION_POLICY


@router.post(
    "/lgtm-images",
    summary="LGTM画像を作成",
    description="base64エンコードされた画像をS3にアップロードし、URLを返します。",
    response_description="アップロードされた画像のURL",
    response_model=LgtmImageCreateResponse,
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
        401: {
            "description": "認証エラー",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid authorization header"}
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
    base_url: Annotated[str, Depends(get_lgtm_images_base_url)],
    token_payload: Annotated[dict[str, Any], Depends(verify_token)],
) -> JSONResponse:
    return await LgtmImageController.create(
        object_storage_repository, base_url, request_body
    )


@router.get(
    "/lgtm-images",
    summary="ランダムなLGTM画像を取得",
    description="ランダムに選択されたLGTM画像のリストを返します。",
    response_description="ランダムに選択されたLGTM画像のリスト",
    response_model=LgtmImageRandomListResponse,
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
        401: {
            "description": "認証エラー",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid authorization header"}
                }
            },
        },
    },
)
async def extract_random_lgtm_images(
    repository: Annotated[
        LgtmImageRepositoryInterface, Depends(create_lgtm_image_repository)
    ],
    base_url: Annotated[str, Depends(get_lgtm_images_base_url)],
    token_payload: Annotated[dict[str, Any], Depends(verify_token)],
) -> JSONResponse:
    return await LgtmImageController.exec(repository, base_url)


@router.get(
    "/lgtm-images/recently-created",
    summary="最近作成されたLGTM画像を取得",
    description="最近作成されたLGTM画像のリストを返します。",
    response_description="最近作成されたLGTM画像のリスト",
    response_model=LgtmImageRecentlyCreatedListResponse,
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
        401: {
            "description": "認証エラー",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid authorization header"}
                }
            },
        },
    },
)
async def retrieve_recently_created_lgtm_images(
    repository: Annotated[
        LgtmImageRepositoryInterface, Depends(create_lgtm_image_repository)
    ],
    base_url: Annotated[str, Depends(get_lgtm_images_base_url)],
    token_payload: Annotated[dict[str, Any], Depends(verify_token)],
) -> JSONResponse:
    return await LgtmImageController.exec_recently_created(repository, base_url)


@router.post(
    "/lgtm-images/search/text",
    summary="テキストからLGTM画像を検索",
    description="ユーザーが入力したテキストと関連する画像を検索して返します。最大9件まで返却されます。",
    response_description="検索結果の画像リスト(関連度の高い順)",
    response_model=LgtmImageSearchResponse,
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
                                "url": "https://lgtm-images.lgtmeow.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp",
                                "similarityScore": 0.9,
                            },
                            {
                                "id": "2",
                                "url": "https://lgtm-images.lgtmeow.com/2021/03/16/23/6947f291-a46e-453c-a230-0d756d7174cb.webp",
                                "similarityScore": 0.8,
                            },
                        ]
                    }
                }
            },
        },
        400: {
            "description": "バリデーションエラー（空クエリなど）",
            "content": {
                "application/json": {
                    "example": {"error": "検索クエリは空白のみにできません"}
                }
            },
        },
        401: {
            "description": "認証エラー",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid authorization header"}
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
async def search_lgtm_images_by_text(
    request_body: TextSearchRequest,
    repository: Annotated[
        LgtmImageSearchRepositoryInterface,
        Depends(create_lgtm_image_search_repository),
    ],
    token_payload: Annotated[dict[str, Any], Depends(verify_token)],
) -> JSONResponse:
    return await LgtmImageController.search_by_text(repository, request_body.query)


@router.post(
    "/lgtm-images/search/image-from-data",
    summary="画像から類似したLGTM画像を検索",
    description="ユーザーから入力された画像と類似する画像を検索して返します。最大9件まで返却されます。",
    response_description="類似画像検索結果のリスト（類似度の高い順）",
    response_model=LgtmImageSearchByImageResponse,
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
                                "url": "https://lgtm-images.lgtmeow.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp",
                                "similarityScore": 0.95,
                            },
                            {
                                "id": "2",
                                "url": "https://lgtm-images.lgtmeow.com/2021/03/16/23/6947f291-a46e-453c-a230-0d756d7174cb.webp",
                                "similarityScore": 0.87,
                            },
                        ]
                    }
                }
            },
        },
        401: {
            "description": "認証エラー",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid authorization header"}
                }
            },
        },
        422: {
            "description": "バリデーションエラー（無効な画像拡張子など）",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "type": "value_error",
                                "loc": ["body", "imageExtension"],
                                "msg": "Value error, Invalid image extension: .invalid",
                                "input": ".invalid",
                            }
                        ]
                    }
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
async def search_by_image(
    request_body: LgtmImageSearchByImageRequest,
    repository: Annotated[
        LgtmImageSearchRepositoryInterface,
        Depends(create_lgtm_image_search_repository),
    ],
    token_payload: Annotated[dict[str, Any], Depends(verify_token)],
) -> JSONResponse:
    return await LgtmImageController.search_by_image(repository, request_body)


@router.post(
    "/lgtm-images/search/image-from-url",
    summary="署名付きURLから類似したLGTM画像を検索",
    description="許可された署名付きURLから画像を取得して類似画像を検索して返します。最大9件まで返却されます。",
    response_description="類似画像検索結果のリスト（類似度の高い順）",
    response_model=LgtmImageSearchByImageResponse,
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
                                "url": "https://lgtm-images.lgtmeow.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp",
                                "similarityScore": 0.95,
                            },
                            {
                                "id": "2",
                                "url": "https://lgtm-images.lgtmeow.com/2021/03/16/23/6947f291-a46e-453c-a230-0d756d7174cb.webp",
                                "similarityScore": 0.87,
                            },
                        ]
                    }
                }
            },
        },
        400: {
            "description": "無効なURLまたは許可されていないドメイン",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_url": {
                            "summary": "無効なURL",
                            "value": {"error": "Invalid URL provided"},
                        },
                        "url_not_accessible": {
                            "summary": "URLにアクセスできない",
                            "value": {"error": "URL not accessible"},
                        },
                    }
                }
            },
        },
        401: {
            "description": "認証エラー",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid authorization header"}
                }
            },
        },
        422: {
            "description": "画像取得失敗または無効な画像形式",
            "content": {
                "application/json": {
                    "examples": {
                        "fetch_failed": {
                            "summary": "画像取得失敗",
                            "value": {"error": "Failed to fetch image from URL"},
                        },
                        "invalid_format": {
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
            "description": "サーバーエラー",
            "content": {
                "application/json": {"example": {"error": "Internal server error"}}
            },
        },
    },
)
async def search_by_image_from_url(
    request_body: LgtmImageSearchByImageFromUrlRequest,
    image_fetch_repository: Annotated[
        ImageFetchRepositoryInterface, Depends(create_image_fetch_repository)
    ],
    repository: Annotated[
        LgtmImageSearchRepositoryInterface,
        Depends(create_lgtm_image_search_repository),
    ],
    token_payload: Annotated[dict[str, Any], Depends(verify_token)],
) -> JSONResponse:
    return await LgtmImageController.search_by_image_from_url(
        image_fetch_repository,
        repository,
        request_body,
    )


@router.post(
    "/lgtm-images/validate-cat",
    summary="猫画像判定",
    description="署名付きURLから画像を取得し、LGTM画像として適切な猫画像かを判定します。不適切なコンテンツ、人の顔、猫以外の画像を検出します。",
    response_description="猫画像判定結果",
    response_model=CatImageValidationResponse,
    tags=["LGTM Images"],
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
                "application/json": {"example": {"error": "Image validation failed"}}
            },
        },
    },
)
async def validate_cat_image(
    request_body: CatImageValidationRequest,
    image_analysis_service: Annotated[
        RekognitionImageAnalysisService, Depends(create_image_analysis_service)
    ],
    image_fetch_repository: Annotated[
        ImageFetchRepositoryInterface, Depends(create_image_fetch_repository)
    ],
    policy: Annotated[CatImageValidationPolicy, Depends(get_validation_policy)],
    token_payload: Annotated[dict[str, Any], Depends(verify_token)],
) -> JSONResponse:
    return await LgtmImageController.validate_cat_image(
        request_body,
        image_analysis_service,
        image_fetch_repository,
        policy,
    )
