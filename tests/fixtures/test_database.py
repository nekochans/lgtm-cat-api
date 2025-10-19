# 絶対厳守：編集前に必ずAI実装ルールを読む

import os
import uuid
from collections.abc import AsyncGenerator

from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from tests.fixtures.planetscale_schema import get_planetscale_schema


def generate_random_db_name() -> str:
    random_suffix = uuid.uuid4().hex[:16]
    return f"test_db_{random_suffix}"


def get_test_database_url(db_name: str | None = None) -> URL:
    user = "test_app_user"
    host = "127.0.0.1"
    port = 3306
    password = os.getenv("TEST_DATABASE_PASSWORD")
    if password is None:
        raise ValueError("TEST_DATABASE_PASSWORD environment variable is not set")

    return URL.create(
        drivername="mysql+asyncmy",
        username=user,
        password=password,
        host=host,
        port=port,
        database=db_name,
    )


async def create_test_database(db_name: str) -> None:
    engine = create_async_engine(get_test_database_url(), echo=False)
    try:
        async with engine.begin() as conn:
            await conn.execute(text(f"CREATE DATABASE `{db_name}`"))
    finally:
        await engine.dispose()


async def drop_test_database(db_name: str) -> None:
    engine = create_async_engine(get_test_database_url(), echo=False)
    try:
        async with engine.begin() as conn:
            await conn.execute(text(f"DROP DATABASE IF EXISTS `{db_name}`"))
    finally:
        await engine.dispose()


async def create_tables_from_schema(engine: AsyncEngine) -> None:
    """PlanetScaleから取得したスキーマを使ってテーブルを作成する.

    Args:
        engine: データベースエンジン

    Raises:
        ValueError: スキーマ取得に失敗した場合
        SQLAlchemyError: テーブル作成に失敗した場合
    """
    schema = await get_planetscale_schema()

    async with engine.begin() as conn:
        for table_name, create_statement in schema.items():
            await conn.execute(text(create_statement))


async def create_test_db_session(db_name: str) -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        get_test_database_url(db_name),
        echo=False,
        pool_pre_ping=True,
    )

    try:
        # スキーマからテーブルを作成
        await create_tables_from_schema(engine)

        # セッションファクトリーを作成
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # セッションを提供
        async with async_session_maker() as session:
            yield session
    finally:
        await engine.dispose()
