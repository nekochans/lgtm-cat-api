# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Any, Protocol


class JwtTokenVerifierRepositoryInterface(Protocol):
    async def verify(self, token: str) -> dict[str, Any]: ...
