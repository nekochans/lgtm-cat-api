# 絶対厳守：編集前に必ずAI実装ルールを読む

import uvicorn
from fastapi import FastAPI

from src.config import get_log_level
from src.log.logger import setup_logging
from src.presentation.middleware.logging_middleware import LoggingMiddleware
from src.presentation.router import lgtm_image_router

# ロギング設定の初期化
setup_logging(log_level=get_log_level())

app = FastAPI(title="LGTM Cat API")

# ミドルウェアの登録
app.add_middleware(LoggingMiddleware)

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
