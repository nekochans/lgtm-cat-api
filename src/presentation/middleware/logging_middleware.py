# 絶対厳守：編集前に必ずAI実装ルールを読む

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from log.logger import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # リクエスト受信ログ
        logger.info(
            "Request received",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else "unknown",
            },
        )

        # 処理時間計測開始
        start_time = time.time()

        response: Response | None = None
        try:
            # リクエスト処理
            response = await call_next(request)
        except Exception as exc:
            # 処理時間計算
            duration_ms = (time.time() - start_time) * 1000

            # 例外発生時のログ（スタックトレース付き）
            logger.error(
                "Request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                    "duration_ms": round(duration_ms, 2),
                },
                exc_info=True,
            )

            # 例外を再送出して上流のエラーハンドリングに任せる
            raise
        finally:
            # レスポンスが正常に返された場合のみ完了ログを出力
            if response is not None:
                # 処理時間計算
                duration_ms = (time.time() - start_time) * 1000

                # レスポンス送信ログ
                logger.info(
                    "Request completed",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": round(duration_ms, 2),
                    },
                )

        # 例外時は raise で抜けるため、ここに到達する時点で response は必ず存在する
        assert response is not None
        return response
