# 絶対厳守:編集前に必ずAI実装ルールを読む

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from log.request_id import generate_request_id, set_request_id


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # X-Request-IdヘッダーからリクエストIDを取得、なければ生成
        request_id = request.headers.get("X-Request-Id") or generate_request_id()
        set_request_id(request_id)

        # リクエスト処理
        response = await call_next(request)

        # レスポンスヘッダーにX-Request-Idを追加
        response.headers["X-Request-Id"] = request_id

        return response
