# 絶対厳守：編集前に必ずAI実装ルールを読む

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.models import LgtmImageModel


async def insert_test_lgtm_images(
    session: AsyncSession,
    count: int = 10,
    start_id: int = 1,
) -> list[LgtmImageModel]:
    now = datetime.now(timezone.utc)
    test_images = [
        LgtmImageModel(
            id=i,
            filename=f"test{i}.webp",
            path=f"/images/test{i}.webp",
            created_at=now,
            updated_at=now,
        )
        for i in range(start_id, start_id + count)
    ]
    session.add_all(test_images)
    await session.commit()
    return test_images
