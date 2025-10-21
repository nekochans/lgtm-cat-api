# 絶対厳守：編集前に必ずAI実装ルールを読む

import uuid
from contextvars import ContextVar
from typing import Optional

# リクエストIDを保持するContextVar
_request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def generate_request_id() -> str:
    return str(uuid.uuid4())


def set_request_id(request_id: str) -> None:
    _request_id_var.set(request_id)


def get_request_id() -> Optional[str]:
    return _request_id_var.get()
