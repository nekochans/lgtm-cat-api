# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Protocol

from domain.lgtm_image_search import DEFAULT_SEARCH_MAX_RESULTS, LgtmImageSearchResult


class LgtmImageSearchRepositoryInterface(Protocol):
    async def search_by_text(
        self, query_text: str, max_results: int = DEFAULT_SEARCH_MAX_RESULTS
    ) -> list[LgtmImageSearchResult]: ...
