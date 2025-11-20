# 絶対厳守:編集前に必ずAI実装ルールを読む

from domain.lgtm_image_search import (
    DEFAULT_SEARCH_MAX_RESULTS,
    LgtmImageSearchResult,
)
from domain.repository.lgtm_image_search_repository_interface import (
    LgtmImageSearchRepositoryInterface,
)
from log.logger import get_logger

logger = get_logger(__name__)


class SearchLgtmImagesByImageUsecase:
    @staticmethod
    async def execute(
        repository: LgtmImageSearchRepositoryInterface,
        image_data: str,
        image_extension: str,
    ) -> list[LgtmImageSearchResult]:
        logger.info("Executing SearchLgtmImagesByImageUsecase")

        results = await repository.search_by_image(
            image_data=image_data,
            image_extension=image_extension,
            max_results=DEFAULT_SEARCH_MAX_RESULTS,
        )

        logger.info(
            "SearchLgtmImagesByImageUsecase completed successfully",
            extra={"results_count": len(results)},
        )

        return results
