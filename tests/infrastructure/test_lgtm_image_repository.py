# 絶対厳守：編集前に必ずAI実装ルールを読む

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from domain.lgtm_image import LgtmImageId
from infrastructure.lgtm_image_repository import LgtmImageRepository
from infrastructure.models import LgtmImageModel


async def insert_test_lgtm_images(
    session: AsyncSession, count: int = 2
) -> list[LgtmImageModel]:
    now = datetime.now()
    images = []
    for i in range(1, count + 1):
        image = LgtmImageModel(
            filename=f"test{i}.webp",
            path=f"/images/test{i}.webp",
            created_at=now,
            updated_at=now,
        )
        session.add(image)
        images.append(image)

    await session.commit()

    # IDを取得するためにリフレッシュ
    for image in images:
        await session.refresh(image)

    return images


@pytest.mark.asyncio
async def test_find_all_ids(test_db_session: AsyncSession) -> None:
    """find_all_idsメソッドのテスト."""
    # テストデータを挿入
    await insert_test_lgtm_images(test_db_session, count=2)

    # リポジトリを作成してテスト
    repository = LgtmImageRepository(test_db_session)
    ids = await repository.find_all_ids()

    # 検証
    assert len(ids) == 2
    assert all(isinstance(id_, int) for id_ in ids)


@pytest.mark.asyncio
async def test_find_by_ids(test_db_session: AsyncSession) -> None:
    """find_by_idsメソッドのテスト."""
    # テストデータを挿入
    images = await insert_test_lgtm_images(test_db_session, count=2)

    # リポジトリを作成してテスト
    repository = LgtmImageRepository(test_db_session)
    ids = [LgtmImageId(images[0].id), LgtmImageId(images[1].id)]
    result = await repository.find_by_ids(ids)

    # 検証
    assert len(result) == 2
    assert result[0]["filename"] == "test1.webp"
    assert result[0]["path"] == "/images/test1.webp"
    assert result[1]["filename"] == "test2.webp"
    assert result[1]["path"] == "/images/test2.webp"


@pytest.mark.asyncio
async def test_find_by_ids_empty_list(test_db_session: AsyncSession) -> None:
    """find_by_idsメソッドで空のIDリストを渡した場合のテスト."""
    repository = LgtmImageRepository(test_db_session)
    result = await repository.find_by_ids([])

    # 検証
    assert result == []


@pytest.mark.asyncio
async def test_find_all_ids_no_data(test_db_session: AsyncSession) -> None:
    """find_all_idsメソッドでデータが0件の場合のテスト."""
    # リポジトリを作成してテスト
    repository = LgtmImageRepository(test_db_session)
    ids = await repository.find_all_ids()

    # 検証
    assert ids == []


@pytest.mark.asyncio
async def test_find_by_ids_nonexistent_ids(test_db_session: AsyncSession) -> None:
    """find_by_idsメソッドで存在しないIDを指定した場合のテスト."""
    # テストデータを挿入
    await insert_test_lgtm_images(test_db_session, count=2)

    # リポジトリを作成してテスト（存在しないIDを指定）
    repository = LgtmImageRepository(test_db_session)
    nonexistent_ids = [LgtmImageId(9999), LgtmImageId(10000)]
    result = await repository.find_by_ids(nonexistent_ids)

    # 検証
    assert result == []


@pytest.mark.asyncio
async def test_find_by_ids_partial_match(test_db_session: AsyncSession) -> None:
    """find_by_idsメソッドで一部のIDのみ存在する場合のテスト."""
    # テストデータを挿入
    images = await insert_test_lgtm_images(test_db_session, count=2)

    # リポジトリを作成してテスト（存在するIDと存在しないIDを混在）
    repository = LgtmImageRepository(test_db_session)
    mixed_ids = [LgtmImageId(images[0].id), LgtmImageId(9999)]
    result = await repository.find_by_ids(mixed_ids)

    # 検証（存在するもののみ返される）
    assert len(result) == 1
    assert result[0]["filename"] == "test1.webp"
    assert result[0]["path"] == "/images/test1.webp"


@pytest.mark.asyncio
async def test_find_recently_created_returns_limited_count(
    test_db_session: AsyncSession,
) -> None:
    """find_recently_createdメソッドでlimit指定時に指定件数が返されることのテスト."""
    # テストデータを異なるcreated_atで挿入
    from datetime import timedelta

    now = datetime.now()
    images = []
    for i in range(1, 6):
        # 各画像を1秒ずつ古くする
        image = LgtmImageModel(
            filename=f"test{i}.webp",
            path=f"/images/test{i}.webp",
            created_at=now - timedelta(seconds=i),
            updated_at=now,
        )
        test_db_session.add(image)
        images.append(image)

    await test_db_session.commit()

    # リポジトリを作成してテスト
    repository = LgtmImageRepository(test_db_session)
    result = await repository.find_recently_created(limit=3)

    # 検証：3件返される
    assert len(result) == 3

    # 検証：created_atの降順（新しい順）でソートされている
    # test1が最新、test2が次、test3が3番目に新しい
    assert result[0]["filename"] == "test1.webp"
    assert result[1]["filename"] == "test2.webp"
    assert result[2]["filename"] == "test3.webp"


@pytest.mark.asyncio
async def test_find_recently_created_returns_all_when_limit_exceeds_total(
    test_db_session: AsyncSession,
) -> None:
    """find_recently_createdメソッドでlimitが総数より大きい場合に全件返されることのテスト."""
    # テストデータを異なるcreated_atで挿入
    from datetime import timedelta

    now = datetime.now()
    images = []
    for i in range(1, 6):
        # 各画像を1秒ずつ古くする
        image = LgtmImageModel(
            filename=f"test{i}.webp",
            path=f"/images/test{i}.webp",
            created_at=now - timedelta(seconds=i),
            updated_at=now,
        )
        test_db_session.add(image)
        images.append(image)

    await test_db_session.commit()

    # リポジトリを作成してテスト
    repository = LgtmImageRepository(test_db_session)
    result_all = await repository.find_recently_created(limit=10)

    # 検証：存在する5件のみ返される
    assert len(result_all) == 5


@pytest.mark.asyncio
async def test_find_recently_created_no_data(test_db_session: AsyncSession) -> None:
    """find_recently_createdメソッドでデータが0件の場合のテスト."""
    # リポジトリを作成してテスト
    repository = LgtmImageRepository(test_db_session)
    result = await repository.find_recently_created(limit=5)

    # 検証：空のリストが返される
    assert result == []
