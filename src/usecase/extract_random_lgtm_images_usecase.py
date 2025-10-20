# 絶対厳守：編集前に必ずAI実装ルールを読む

import random

from src.domain.lgtm_image import DEFAULT_RANDOM_IMAGES_LIMIT, LgtmImage
from src.domain.lgtm_image_errors import ErrRecordCount
from src.domain.lgtm_image_object import create_lgtm_image
from src.domain.repository.lgtm_image_repository_interface import (
    LgtmImageRepositoryInterface,
)
from src.log.logger import get_logger

logger = get_logger(__name__)


class ExtractRandomLgtmImagesUsecase:
    @staticmethod
    async def execute(
        repository: LgtmImageRepositoryInterface,
        base_url: str,
        limit: int = DEFAULT_RANDOM_IMAGES_LIMIT,
    ) -> list[LgtmImage]:
        logger.info("Executing ExtractRandomLgtmImagesUsecase", extra={"limit": limit})

        ids = await repository.find_all_ids()

        if len(ids) < limit:
            raise ErrRecordCount()

        random_ids = random.sample(ids, limit)

        image_objects = await repository.find_by_ids(random_ids)

        images = [create_lgtm_image(obj, base_url) for obj in image_objects]

        logger.info(
            "ExtractRandomLgtmImagesUsecase completed successfully",
            extra={"images_count": len(images)},
        )

        return images
