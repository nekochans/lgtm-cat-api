# 絶対厳守：編集前に必ずAI実装ルールを読む

import uvicorn
from fastapi import FastAPI

from src.presentation.router import lgtm_image_router

app = FastAPI(title="LGTM Cat API")

# ルーターの登録
app.include_router(lgtm_image_router.router)


def start() -> None:
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start()
