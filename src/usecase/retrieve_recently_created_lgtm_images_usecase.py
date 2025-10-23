# 絶対厳守：編集前に必ずAI実装ルールを読む

from domain.lgtm_image import DEFAULT_RANDOM_IMAGES_LIMIT, LgtmImage
from domain.lgtm_image_errors import ErrRecordCount
from domain.lgtm_image_object import create_lgtm_image
from domain.repository.lgtm_image_repository_interface import (
    LgtmImageRepositoryInterface,
)
from log.logger import get_logger

logger = get_logger(__name__)


class RetrieveRecentlyCreatedLgtmImagesUsecase:
    @staticmethod
    async def execute(
        repository: LgtmImageRepositoryInterface,
        base_url: str,
        limit: int = DEFAULT_RANDOM_IMAGES_LIMIT,
    ) -> list[LgtmImage]:
        logger.info(
            "Executing RetrieveRecentlyCreatedLgtmImagesUsecase",
            extra={"limit": limit},
        )

        image_objects = await repository.find_recently_created(limit)

        if len(image_objects) < limit:
            raise ErrRecordCount()

        images = [create_lgtm_image(obj, base_url) for obj in image_objects]

        logger.info(
            "RetrieveRecentlyCreatedLgtmImagesUsecase completed successfully",
            extra={"images_count": len(images)},
        )

        return images
