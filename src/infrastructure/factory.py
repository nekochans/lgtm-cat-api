# 絶対厳守:編集前に必ずAI実装ルールを読む

"""リポジトリインスタンス生成用のファクトリーモジュール.

このモジュールはpresentation層がinfrastructure層の具体的な実装に
直接依存しないようにするためのファクトリー関数を提供します。
"""

from sqlalchemy.ext.asyncio import AsyncSession

from domain.repository.lgtm_image_repository_interface import (
    LgtmImageRepositoryInterface,
)
from infrastructure.lgtm_image_repository import LgtmImageRepository


def create_lgtm_image_repository(
    session: AsyncSession,
) -> LgtmImageRepositoryInterface:
    """LGTM画像リポジトリのインスタンスを生成.

    Args:
        session: 非同期データベースセッション

    Returns:
        LgtmImageRepositoryInterface: LGTM画像リポジトリインスタンス
    """
    return LgtmImageRepository(session)
