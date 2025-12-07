# 絶対厳守：編集前に必ずAI実装ルールを読む

import random

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from domain.lgtm_image_errors import ErrRecordCount
from infrastructure.lgtm_image_repository import LgtmImageRepository
from tests.fixtures.test_data_helpers import insert_test_lgtm_images
from usecase.extract_random_lgtm_markdown_usecase import (
    ExtractRandomLgtmMarkdownUsecase,
)


class TestExtractRandomLgtmMarkdownUsecase:
    @pytest.mark.asyncio
    async def test_execute_returns_markdown_format(
        self, test_db_session: AsyncSession
    ) -> None:
        """正常系: [![LGTMeow](url)](https://lgtmeow.com) 形式の文字列を返すことを検証."""
        # Arrange - DBに10件のテストデータを挿入
        await insert_test_lgtm_images(test_db_session, count=10)

        repository = LgtmImageRepository(test_db_session)
        base_url = "example.com"
        lgtmeow_url = "https://lgtmeow.com"
        random.seed(42)  # ランダム性を固定

        # Act
        result = await ExtractRandomLgtmMarkdownUsecase.execute(
            repository=repository,
            base_url=base_url,
            lgtmeow_url=lgtmeow_url,
        )

        # Assert - 文字列型であることを検証
        assert isinstance(result, str)
        assert len(result) > 0

        # Assert - マークダウン形式のフォーマット検証
        assert result.startswith("[![LGTMeow](")
        assert result.endswith(")](https://lgtmeow.com)")
        assert f"https://{base_url}" in result

    @pytest.mark.asyncio
    async def test_execute_raises_err_record_count_when_no_images(
        self, test_db_session: AsyncSession
    ) -> None:
        """異常系: 画像が0件の場合にErrRecordCountが発生することを検証."""
        # Arrange - テストデータを挿入しない（0件）
        repository = LgtmImageRepository(test_db_session)
        base_url = "example.com"
        lgtmeow_url = "https://lgtmeow.com"

        # Act & Assert
        with pytest.raises(ErrRecordCount):
            await ExtractRandomLgtmMarkdownUsecase.execute(
                repository=repository,
                base_url=base_url,
                lgtmeow_url=lgtmeow_url,
            )
