# 絶対厳守：編集前に必ずAI実装ルールを読む

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from src.presentation.controller.response_helper import create_json_response


class HealthCheckResponse(BaseModel):
    status_code: int = Field(..., alias="statusCode", description="ステータスコード")


class HealthCheckController:
    @staticmethod
    def check() -> JSONResponse:
        response = HealthCheckResponse(statusCode=200)
        return create_json_response(response, status_code=200)
