# 絶対厳守：編集前に必ずAI実装ルールを読む

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.lgtm_image import LgtmImageId
from src.domain.lgtm_image_object import LgtmImageObject
from src.domain.repository.lgtm_image_repository_interface import (
    LgtmImageRepositoryInterface,
)
from src.infrastructure.models import LgtmImageModel
from src.log.logger import get_logger

logger = get_logger(__name__)


class LgtmImageRepository(LgtmImageRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_all_ids(self) -> list[LgtmImageId]:
        logger.info("Finding all LGTM image IDs")
        result = await self._session.execute(select(LgtmImageModel.id))
        ids = result.scalars().all()
        lgtm_image_ids = [LgtmImageId(id_) for id_ in ids]
        logger.info("Found LGTM image IDs", extra={"count": len(lgtm_image_ids)})
        return lgtm_image_ids

    async def find_by_ids(self, ids: list[LgtmImageId]) -> list[LgtmImageObject]:
        logger.info("Finding LGTM images by IDs", extra={"ids_count": len(ids)})

        # IDのリストが空の場合は空リストを返す
        if not ids:
            logger.info("Found LGTM images", extra={"count": 0})
            return []

        # int型に変換してクエリ実行
        int_ids = [int(id_) for id_ in ids]
        result = await self._session.execute(
            select(LgtmImageModel).where(LgtmImageModel.id.in_(int_ids))
        )
        models = result.scalars().all()

        # DBモデルをドメインエンティティに変換
        image_objects = [
            LgtmImageObject(
                id=LgtmImageId(model.id),
                path=model.path,
                filename=model.filename,
            )
            for model in models
        ]

        logger.info("Found LGTM images", extra={"count": len(image_objects)})
        return image_objects

    async def find_recently_created(self, limit: int) -> list[LgtmImageObject]:
        logger.info("Finding recently created LGTM images", extra={"limit": limit})

        result = await self._session.execute(
            select(LgtmImageModel)
            .order_by(LgtmImageModel.created_at.desc())
            .limit(limit)
        )
        models = result.scalars().all()

        # DBモデルをドメインエンティティに変換
        image_objects = [
            LgtmImageObject(
                id=LgtmImageId(model.id),
                path=model.path,
                filename=model.filename,
            )
            for model in models
        ]

        logger.info(
            "Found recently created LGTM images", extra={"count": len(image_objects)}
        )
        return image_objects
