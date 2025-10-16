# 絶対厳守：編集前に必ずAI実装ルールを読む

from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


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
