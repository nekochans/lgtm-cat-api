# 絶対厳守:編集前に必ずAI実装ルールを読む


from starlette.types import ASGIApp, Message, Receive, Scope, Send

from log.request_id import generate_request_id, set_request_id


class RequestIdMiddleware:
    """純粋なASGIミドルウェアとして実装（SSEストリーミングとの互換性のため）"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # MCPエンドポイント（SSE、Streamable HTTP）はリクエストID処理をスキップ
        # LoggingMiddlewareでログを出力しないため、リクエストIDを生成・設定する意味がない
        path = scope.get("path", "")
        if path.startswith("/sse") or path.startswith("/mcp"):
            await self.app(scope, receive, send)
            return

        # ヘッダーからX-Request-Idを取得、なければ生成
        headers = dict(scope.get("headers", []))
        request_id = headers.get(b"x-request-id", b"").decode() or generate_request_id()
        set_request_id(request_id)

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                # レスポンスヘッダーにX-Request-Idを追加
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
