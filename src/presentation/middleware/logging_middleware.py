# 絶対厳守：編集前に必ずAI実装ルールを読む

import time

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from log.logger import get_logger

logger = get_logger(__name__)


class LoggingMiddleware:
    """純粋なASGIミドルウェアとして実装（SSEストリーミングとの互換性のため）"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # SSEエンドポイントはロギングをスキップ
        path = scope.get("path", "")
        if path.startswith("/sse"):
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        client = scope.get("client")
        client_host = client[0] if client else "unknown"

        # リクエスト受信ログ
        logger.info(
            "Request received",
            extra={
                "method": method,
                "path": path,
                "client_host": client_host,
            },
        )

        # 処理時間計測開始
        start_time = time.time()
        status_code: int | None = None

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            # 処理時間計算
            duration_ms = (time.time() - start_time) * 1000

            # 例外発生時のログ（スタックトレース付き）
            logger.error(
                "Request failed",
                extra={
                    "method": method,
                    "path": path,
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                    "duration_ms": round(duration_ms, 2),
                },
                exc_info=True,
            )
            raise
        else:
            # 処理時間計算
            duration_ms = (time.time() - start_time) * 1000

            # レスポンス送信ログ
            logger.info(
                "Request completed",
                extra={
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )
