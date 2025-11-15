# 絶対厳守：編集前に必ずAI実装ルールを読む

from domain.lgtm_image_search import (
    DEFAULT_SEARCH_MAX_RESULTS,
    LgtmImageSearchResult,
    MAX_QUERY_LENGTH,
)
from domain.lgtm_image_errors import ErrInvalidSearchQuery
from domain.repository.lgtm_image_search_repository_interface import (
    LgtmImageSearchRepositoryInterface,
)
from log.logger import get_logger

import unicodedata

logger = get_logger(__name__)


class SearchLgtmImagesByTextUsecase:
    @staticmethod
    def _normalize_query_text(query_text: str) -> str:
        # 1. Unicode正規化（NFKC）- 全角/半角、濁点の統一
        normalized = unicodedata.normalize("NFKC", query_text)

        # 2. トリムと空白の正規化 - 連続する空白を単一スペースに
        normalized = " ".join(normalized.strip().split())

        return normalized

    @staticmethod
    def _validate_query_text(query_text: str) -> None:
        # 空文字チェック
        if not query_text:
            logger.warning("Empty query text provided after normalization")
            raise ErrInvalidSearchQuery("Search query cannot be empty")

        # 文字数制限チェック
        if len(query_text) > MAX_QUERY_LENGTH:
            logger.warning(
                "Query text exceeds maximum length",
                extra={
                    "query_length": len(query_text),
                    "max_length": MAX_QUERY_LENGTH,
                },
            )
            raise ErrInvalidSearchQuery(
                f"Search query must be {MAX_QUERY_LENGTH} characters or less"
            )

    @staticmethod
    async def execute(
        repository: LgtmImageSearchRepositoryInterface,
        query_text: str,
    ) -> list[LgtmImageSearchResult]:
        logger.info("Executing SearchLgtmImagesByTextUsecase")

        normalized_query = SearchLgtmImagesByTextUsecase._normalize_query_text(
            query_text
        )

        SearchLgtmImagesByTextUsecase._validate_query_text(normalized_query)

        logger.info(
            "Query normalized and validated",
            extra={"query_length": len(normalized_query)},
        )

        results = await repository.search_by_text(
            normalized_query, max_results=DEFAULT_SEARCH_MAX_RESULTS
        )

        logger.info(
            "SearchLgtmImagesByTextUsecase completed successfully",
            extra={"results_count": len(results)},
        )

        return results
