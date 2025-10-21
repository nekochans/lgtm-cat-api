# 絶対厳守：編集前に必ずAI実装ルールを読む

import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # リクエストIDがあれば追加
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # 追加のカスタムフィールドを含める
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
                "request_id",
            ]:
                log_data[key] = value

        # 例外情報があれば追加
        if record.exc_info:
            log_data["traceback"] = "".join(
                traceback.format_exception(*record.exc_info)
            )

        return json.dumps(log_data, ensure_ascii=False, default=str)
