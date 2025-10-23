# 絶対厳守：編集前に必ずAI実装ルールを読む

import os
import ssl
from collections.abc import AsyncGenerator

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def get_database_url() -> URL:
    database_user = os.getenv("DATABASE_USER")
    if database_user is None:
        raise ValueError("DATABASE_USER environment variable is not set")

    database_password = os.getenv("DATABASE_PASSWORD")
    if database_password is None:
        raise ValueError("DATABASE_PASSWORD environment variable is not set")

    database_host = os.getenv("DATABASE_HOST")
    if database_host is None:
        raise ValueError("DATABASE_HOST environment variable is not set")

    database_name = os.getenv("DATABASE_NAME")
    if database_name is None:
        raise ValueError("DATABASE_NAME environment variable is not set")

    # 接続URLを構築
    return URL.create(
        drivername="mysql+asyncmy",
        username=database_user,
        password=database_password,
        host=database_host,
        database=database_name,
    )


def get_ssl_context() -> ssl.SSLContext:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True

    return ssl_context


# 非同期エンジンの作成
engine = create_async_engine(
    get_database_url(),
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    pool_recycle=1800,
    pool_timeout=30,
    connect_args={
        "ssl": get_ssl_context(),
    },
)

# セッションファクトリーの作成
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_db_session() -> AsyncGenerator[AsyncSession, None]:
    """データベースセッションを取得する依存性注入用の関数."""
    async with AsyncSessionLocal() as session:
        yield session
