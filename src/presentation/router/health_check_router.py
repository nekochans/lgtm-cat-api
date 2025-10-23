# 絶対厳守：編集前に必ずAI実装ルールを読む
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from presentation.controller.health_check_controller import HealthCheckController


router = APIRouter()


@router.get(
    "/health-checks",
    summary="ヘルスチェック",
    description="ステータスコード200を返します。",
    response_description="ヘルスチェックの結果",
    tags=["Health Check"],
    responses={
        200: {
            "description": "成功時のレスポンス",
            "content": {"application/json": {"example": {"statusCode": 200}}},
        }
    },
)
async def check() -> JSONResponse:
    return HealthCheckController.check()
