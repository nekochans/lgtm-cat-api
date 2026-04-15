# 絶対厳守：編集前に必ずAI実装ルールを読む

import sys
import uvicorn
from contextlib import asynccontextmanager
from typing import AsyncIterator
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
from presentation.router import (
    cat_image_router,
    lgtm_image_router,
    lgtm_image_v2_router,
    mcp_sse_router,
)
from presentation.mcp import mcp_http_transport

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


# FastAPIアプリケーションのlifespan設定
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """FastAPIアプリケーションのライフサイクル管理.

    StreamableHTTPSessionManagerを初期化してタスクグループを作成します。
    これにより、`app.mount()`でマウントされたMCP HTTPトランスポートが正常に動作します。
    """
    # StreamableHTTPSessionManagerを初期化
    async with mcp_http_transport.session_manager.run():
        yield


# FastAPIアプリケーション作成
app = FastAPI(title="LGTM Cat API", lifespan=lifespan)


# 例外ハンドラの登録（X-Request-Idヘッダーを追加）
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> Response:
    """バリデーション例外ハンドラ"""
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: Exception) -> Response:
    """HTTP例外ハンドラ"""
    # 型アサーション: add_exception_handlerで登録した型が渡される
    http_exc = (
        exc
        if isinstance(exc, StarletteHTTPException)
        else StarletteHTTPException(status_code=500)
    )
    return JSONResponse(
        status_code=http_exc.status_code,
        content={"detail": http_exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> Response:
    """一般例外ハンドラ"""
    # Sentryに例外を送信
    request_id = get_request_id()
    extra_context = {"request_id": request_id} if request_id else None
    capture_exception(exc, extra=extra_context)

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


# ミドルウェアの登録（後に登録したものが先に実行される）
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIdMiddleware)

# ルーターの登録
app.include_router(cat_image_router.router)
app.include_router(lgtm_image_router.router)
app.include_router(lgtm_image_v2_router.router)
app.include_router(health_check_router.router)

# MCP SSEトランスポート（認証不要）
# /sseエンドポイントをルーターとして登録（FastAPIの例外ハンドラーが動作）
app.include_router(mcp_sse_router.router)

# SSEトランスポート用のPOSTメッセージハンドラをマウント
app.mount(mcp_sse_router.SSE_MESSAGES_PATH, mcp_sse_router.sse.handle_post_message)

# MCP HTTPトランスポート（認証不要）
# /mcpエンドポイントをASGIアプリとしてマウント（低レベルAPI使用）
app.mount("/mcp", mcp_http_transport.http_app)


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
