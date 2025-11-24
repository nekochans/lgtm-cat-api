# 絶対厳守：編集前に必ずAI実装ルールを読む
import base64

from domain.image_format import mime_type_to_extension
from domain.lgtm_image_search import (
    DEFAULT_SEARCH_MAX_RESULTS,
    LgtmImageSearchResult,
)
from domain.repository.image_fetch_repository_interface import (
    ImageFetchRepositoryInterface,
)
from domain.repository.lgtm_image_search_repository_interface import (
    LgtmImageSearchRepositoryInterface,
)
from log.logger import get_logger
from log.url_sanitizer import sanitize_url_for_logging

logger = get_logger(__name__)


class SearchLgtmImagesByImageFromUrlUsecase:
    @staticmethod
    async def execute(
        image_fetch_repository: ImageFetchRepositoryInterface,
        search_repository: LgtmImageSearchRepositoryInterface,
        image_url: str,
    ) -> list[LgtmImageSearchResult]:
        safe_url = sanitize_url_for_logging(image_url)
        logger.info(
            "Executing SearchLgtmImagesByImageFromUrlUsecase",
            extra={"image_url": safe_url},
        )

        # 外部URLから画像を取得（MIMEタイプも含む）
        fetched_image = await image_fetch_repository.fetch_image(image_url)

        logger.info(
            f"Successfully fetched image from URL ({len(fetched_image['data'])} bytes, type: {fetched_image['mime_type']})",
            extra={
                "image_url": safe_url,
                "size": len(fetched_image["data"]),
                "mime_type": fetched_image["mime_type"],
            },
        )

        # MIMEタイプから拡張子を取得
        image_extension = mime_type_to_extension(fetched_image["mime_type"])

        # バイトデータをbase64エンコード
        image_data = base64.b64encode(fetched_image["data"]).decode("utf-8")

        logger.info(
            "Encoded image to base64",
            extra={"image_extension": image_extension},
        )

        results = await search_repository.search_by_image(
            image_data=image_data,
            image_extension=image_extension,
            max_results=DEFAULT_SEARCH_MAX_RESULTS,
        )

        logger.info(
            "SearchLgtmImagesByImageFromUrlUsecase completed successfully",
            extra={"results_count": len(results)},
        )

        return results
