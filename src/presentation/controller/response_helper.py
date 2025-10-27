# 絶対厳守：編集前に必ずAI実装ルールを読む
from typing import Optional

from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from sentry.initializer import capture_exception
from log.request_id import get_request_id


def create_json_response(
    response_body: BaseModel,
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=response_body.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
            exclude_unset=True,
        ),
    )


def create_error_response(
    error: Exception, extra: Optional[dict[str, str]] = None
) -> JSONResponse:
    # request_idを自動的に取得してコンテキストに追加
    request_id = get_request_id()
    context = extra.copy() if extra else {}
    if request_id:
        context["request_id"] = request_id

    capture_exception(error, extra=context if context else None)

    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )
