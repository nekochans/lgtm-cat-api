# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Protocol

from domain.lgtm_image_search import LgtmImageSearchResult


class LgtmImageSearchRepositoryInterface(Protocol):
    async def search_by_text(
        self, query_text: str, max_results: int = 9
    ) -> list[LgtmImageSearchResult]: ...
