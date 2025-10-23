# 絶対厳守：編集前に必ずAI実装ルールを読む

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from domain.lgtm_image import DEFAULT_RANDOM_IMAGES_LIMIT
from domain.lgtm_image_errors import ErrRecordCount
from infrastructure.lgtm_image_repository import LgtmImageRepository
from usecase.retrieve_recently_created_lgtm_images_usecase import (
    RetrieveRecentlyCreatedLgtmImagesUsecase,
)
from tests.fixtures.test_data_helpers import insert_test_lgtm_images


class TestRetrieveRecentlyCreatedLgtmImagesUsecase:
    @pytest.mark.asyncio
    async def test_execute_success_with_correct_data_transformation(
        self, test_db_session: AsyncSession
    ) -> None:
        """正常系: 最近作成された画像を取得し、データが正しく変換される."""
        # Arrange - DBに10件のテストデータを挿入
        await insert_test_lgtm_images(test_db_session, count=10)

        repository = LgtmImageRepository(test_db_session)
        base_url = "cdn.example.com"

        # Act - デフォルトlimitで取得
        result = await RetrieveRecentlyCreatedLgtmImagesUsecase.execute(
            repository=repository,
            base_url=base_url,
        )

        # Assert - 件数とデータ型の確認
        assert len(result) == DEFAULT_RANDOM_IMAGES_LIMIT
        assert all(isinstance(image, dict) for image in result)
        assert all("id" in image and "url" in image for image in result)

        # URLとIDの詳細な形式確認
        for image in result:
            # URLの形式が正しいか確認
            assert image["url"].startswith(f"https://{base_url}")
            assert "/" in image["url"]  # pathが含まれている
            assert image["url"].endswith(".webp")

            # IDが文字列として正しく設定されているか確認
            assert isinstance(image["id"], str)
            assert image["id"].isdigit()

    @pytest.mark.asyncio
    async def test_execute_success_with_custom_limit(
        self, test_db_session: AsyncSession
    ) -> None:
        """正常系: カスタムlimitで最近作成された画像を取得できる."""
        # Arrange - DBに10件のテストデータを挿入
        await insert_test_lgtm_images(test_db_session, count=10)

        repository = LgtmImageRepository(test_db_session)
        custom_limit = 3
        base_url = "example.com"

        # Act
        result = await RetrieveRecentlyCreatedLgtmImagesUsecase.execute(
            repository=repository,
            base_url=base_url,
            limit=custom_limit,
        )

        # Assert
        assert len(result) == custom_limit
        assert all(isinstance(image, dict) for image in result)
        assert all("id" in image and "url" in image for image in result)

    @pytest.mark.asyncio
    async def test_execute_returns_results_in_recent_order(
        self, test_db_session: AsyncSession
    ) -> None:
        """正常系: 結果が作成日時の降順（新しい順）で返される."""
        from datetime import datetime, timedelta, timezone

        from infrastructure.models import LgtmImageModel

        # Arrange - テストデータを異なるcreated_atで挿入
        now = datetime.now(timezone.utc)
        images = []
        for i in range(1, 6):
            # 各画像を1秒ずつ古くする
            image = LgtmImageModel(
                id=i,
                filename=f"recent{i}.webp",
                path=f"/images/recent{i}.webp",
                created_at=now - timedelta(seconds=i),
                updated_at=now,
            )
            test_db_session.add(image)
            images.append(image)

        await test_db_session.commit()

        repository = LgtmImageRepository(test_db_session)
        base_url = "example.com"
        limit = 3

        # Act
        result = await RetrieveRecentlyCreatedLgtmImagesUsecase.execute(
            repository=repository,
            base_url=base_url,
            limit=limit,
        )

        # Assert - 最新の3件が返され、新しい順に並んでいる
        assert len(result) == 3
        # ID順で新しい順（1, 2, 3）
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"
        assert result[2]["id"] == "3"

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_no_data(
        self, test_db_session: AsyncSession
    ) -> None:
        """異常系: データが0件の場合はErrRecordCountを発生させる."""
        # Arrange - DBにデータを挿入しない
        repository = LgtmImageRepository(test_db_session)
        base_url = "example.com"

        # Act & Assert
        with pytest.raises(ErrRecordCount):
            await RetrieveRecentlyCreatedLgtmImagesUsecase.execute(
                repository=repository,
                base_url=base_url,
            )

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_insufficient_records(
        self, test_db_session: AsyncSession
    ) -> None:
        """異常系: limitが総数より大きい場合はErrRecordCountを発生させる."""
        # Arrange - DBに5件のテストデータを挿入
        await insert_test_lgtm_images(test_db_session, count=5)

        repository = LgtmImageRepository(test_db_session)
        base_url = "example.com"
        limit = 20  # 5件しかないのに20件要求

        # Act & Assert
        with pytest.raises(ErrRecordCount):
            await RetrieveRecentlyCreatedLgtmImagesUsecase.execute(
                repository=repository,
                base_url=base_url,
                limit=limit,
            )
