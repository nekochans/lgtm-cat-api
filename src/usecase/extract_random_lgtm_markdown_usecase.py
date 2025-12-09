# 絶対厳守：編集前に必ずAI実装ルールを読む

import random

from domain.lgtm_image_errors import ErrRecordCount
from domain.lgtm_image_object import create_lgtm_image
from domain.repository.lgtm_image_repository_interface import (
    LgtmImageRepositoryInterface,
)
from log.logger import get_logger

logger = get_logger(__name__)


class ExtractRandomLgtmMarkdownUsecase:
    @staticmethod
    async def execute(
        repository: LgtmImageRepositoryInterface,
        base_url: str,
        lgtmeow_url: str,
    ) -> str:
        logger.info("Executing ExtractRandomLgtmMarkdownUsecase")

        ids = await repository.find_all_ids()

        if len(ids) < 1:
            raise ErrRecordCount()

        random_id = random.choice(ids)

        image_objects = await repository.find_by_ids([random_id])

        if len(image_objects) == 0:
            raise ErrRecordCount()

        lgtm_image = create_lgtm_image(image_objects[0], base_url)

        markdown = f"[![LGTMeow]({lgtm_image['url']})]({lgtmeow_url})"

        logger.info(
            "ExtractRandomLgtmMarkdownUsecase completed successfully",
            extra={"markdown": markdown},
        )

        return markdown
