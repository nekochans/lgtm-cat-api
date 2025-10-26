# 絶対厳守：編集前に必ずAI実装ルールを読む

import sys
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from presentation.router import health_check_router
from config import (
    get_log_level,
    get_sentry_dsn,
    get_sentry_environment,
    validate_required_config,
)
from sentry.initializer import capture_exception, init_sentry
from log.logger import setup_logging
from log.request_id import get_request_id
from presentation.middleware.logging_middleware import LoggingMiddleware
from presentation.middleware.request_id_middleware import RequestIdMiddleware
from presentation.router import lgtm_image_router

# 必須の環境変数を検証（起動時にfail-fast）
try:
    validate_required_config()
except RuntimeError as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)

# ロギング設定の初期化
setup_logging(log_level=get_log_level())

# Sentryの初期化
# Sentryはエラー監視機能なので、初期化に失敗してもアプリケーションは継続起動する
try:
    init_sentry(
        dsn=get_sentry_dsn(),
        environment=get_sentry_environment(),
    )
except Exception as e:
    print(f"WARNING: Failed to initialize Sentry: {e}", file=sys.stderr)
    print("Application will continue without Sentry error monitoring.", file=sys.stderr)

app = FastAPI(title="LGTM Cat API")


# 例外ハンドラの登録（X-Request-Idヘッダーを追加）
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> Response:
    """バリデーション例外ハンドラ - X-Request-Idヘッダーを追加"""
    response = JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )
    request_id = get_request_id()
    if request_id:
        response.headers["X-Request-Id"] = request_id
    return response


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
    # Sentryに例外を送信
    request_id = get_request_id()
    extra_context = {"request_id": request_id} if request_id else None
    capture_exception(exc, extra=extra_context)

    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )
    if request_id:
        response.headers["X-Request-Id"] = request_id
    return response


# ミドルウェアの登録（後に登録したものが先に実行される）
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIdMiddleware)

# ルーターの登録
app.include_router(lgtm_image_router.router)
app.include_router(health_check_router.router)


def start() -> None:
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        access_log=False,
    )


if __name__ == "__main__":
    start()
