# 絶対厳守：編集前に必ずAI実装ルールを読む

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.config import get_log_level
from src.log.logger import setup_logging
from src.log.request_id import get_request_id
from src.presentation.middleware.logging_middleware import LoggingMiddleware
from src.presentation.middleware.request_id_middleware import RequestIdMiddleware
from src.presentation.router import lgtm_image_router

# ロギング設定の初期化
setup_logging(log_level=get_log_level())

app = FastAPI(title="LGTM Cat API")


# 例外ハンドラの登録（X-Request-Idヘッダーを追加）
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: Exception) -> Response:
    """HTTP例外ハンドラ - X-Request-Idヘッダーを追加"""
    # 型アサーション: add_exception_handlerで登録した型が渡される
    http_exc = (
        exc
        if isinstance(exc, StarletteHTTPException)
        else StarletteHTTPException(status_code=500)
    )
    response = JSONResponse(
        status_code=http_exc.status_code,
        content={"detail": http_exc.detail},
    )
    request_id = get_request_id()
    if request_id:
        response.headers["X-Request-Id"] = request_id
    return response


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> Response:
    """一般例外ハンドラ - X-Request-Idヘッダーを追加"""
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )
    request_id = get_request_id()
    if request_id:
        response.headers["X-Request-Id"] = request_id
    return response


# ミドルウェアの登録（後に登録したものが先に実行される）
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIdMiddleware)

# ルーターの登録
app.include_router(lgtm_image_router.router)


def start() -> None:
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        access_log=False,
    )


if __name__ == "__main__":
    start()
