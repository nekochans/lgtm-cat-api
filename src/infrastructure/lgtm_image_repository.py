# 絶対厳守：編集前に必ずAI実装ルールを読む

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.lgtm_image import LgtmImageId
from src.domain.lgtm_image_object import LgtmImageObject
from src.domain.repository.lgtm_image_repository_interface import (
    LgtmImageRepositoryInterface,
)
from src.infrastructure.models import LgtmImageModel


class LgtmImageRepository(LgtmImageRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_all_ids(self) -> list[LgtmImageId]:
        result = await self._session.execute(select(LgtmImageModel.id))
        ids = result.scalars().all()
        return [LgtmImageId(id_) for id_ in ids]

    async def find_by_ids(self, ids: list[LgtmImageId]) -> list[LgtmImageObject]:
        # IDのリストが空の場合は空リストを返す
        if not ids:
            return []

        # int型に変換してクエリ実行
        int_ids = [int(id_) for id_ in ids]
        result = await self._session.execute(
            select(LgtmImageModel).where(LgtmImageModel.id.in_(int_ids))
        )
        models = result.scalars().all()

        # DBモデルをドメインエンティティに変換
        return [
            LgtmImageObject(
                id=LgtmImageId(model.id),
                path=model.path,
                filename=model.filename,
            )
            for model in models
        ]
