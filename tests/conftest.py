# 絶対厳守：編集前に必ずAI実装ルールを読む

import logging
from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from tests.fixtures.test_database import (
    create_test_database,
    drop_test_database,
    generate_random_db_name,
    create_test_db_session,
)

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    # ランダムなDB名を生成
    db_name = generate_random_db_name()

    # テストデータベース作成成功フラグ
    created = False

    try:
        # テストデータベースを作成
        await create_test_database(db_name)
        created = True

        # セッションを取得して提供
        async for session in create_test_db_session(db_name):
            yield session
    finally:
        # データベース作成に成功した場合のみ削除を試みる
        if created:
            try:
                await drop_test_database(db_name)
            except Exception as e:
                # 削除失敗をログに記録するが、元のエラーをマスクしないため再送出しない
                logger.warning(f"Failed to drop test database '{db_name}': {e}")
