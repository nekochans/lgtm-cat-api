# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Protocol

from src.domain.lgtm_image import LgtmImageId
from src.domain.lgtm_image_object import LgtmImageObject


class LgtmImageRepositoryInterface(Protocol):
    async def find_all_ids(self) -> list[LgtmImageId]: ...

    async def find_by_ids(self, ids: list[LgtmImageId]) -> list[LgtmImageObject]: ...

    async def find_recently_created(self, limit: int) -> list[LgtmImageObject]: ...
