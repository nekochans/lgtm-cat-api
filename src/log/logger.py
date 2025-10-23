# 絶対厳守：編集前に必ずAI実装ルールを読む

import logging
import os
from typing import Optional

from log.request_id import get_request_id
from log.formatter import JsonFormatter


class RequestIdFilter(logging.Filter):
    """リクエストIDをログレコードに追加するフィルター"""

    def filter(self, record: logging.LogRecord) -> bool:
        request_id = get_request_id()
        if request_id:
            setattr(record, "request_id", request_id)
        return True


def setup_logging(log_level: Optional[str] = None) -> None:
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")

    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 既存のハンドラーをクリア
    root_logger.handlers.clear()

    # StreamHandlerの作成
    handler = logging.StreamHandler()
    handler.setLevel(log_level)

    # JSONフォーマッターの設定
    formatter = JsonFormatter()
    handler.setFormatter(formatter)

    # リクエストIDフィルターの追加
    handler.addFilter(RequestIdFilter())

    # ハンドラーをルートロガーに追加
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
