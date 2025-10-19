# 絶対厳守：編集前に必ずAI実装ルールを読む

import random

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.lgtm_image import DEFAULT_RANDOM_IMAGES_LIMIT
from src.domain.lgtm_image_errors import ErrRecordCount
from src.infrastructure.lgtm_image_repository import LgtmImageRepository
from src.usecase.extract_random_lgtm_images_usecase import (
    ExtractRandomLgtmImagesUsecase,
)
from tests.fixtures.test_data_helpers import insert_test_lgtm_images


class TestExtractRandomLgtmImagesUsecase:
    @pytest.mark.asyncio
    async def test_execute_success_with_default_limit(
        self, test_db_session: AsyncSession
    ) -> None:
        """正常系: デフォルトのlimitでランダムな画像を取得できる."""
        # Arrange - DBに10件のテストデータを挿入
        await insert_test_lgtm_images(test_db_session, count=10)

        repository = LgtmImageRepository(test_db_session)
        base_url = "example.com"
        random.seed(42)  # ランダム性を固定

        # Act
        result = await ExtractRandomLgtmImagesUsecase.execute(
            repository=repository,
            base_url=base_url,
        )

        # Assert
        assert len(result) == DEFAULT_RANDOM_IMAGES_LIMIT
        assert all(isinstance(image, dict) for image in result)
        assert all("id" in image and "url" in image for image in result)

        # URLが正しい形式であることを確認
        for image in result:
            assert image["url"].startswith(f"https://{base_url}")
            assert image["url"].endswith(".webp")

    @pytest.mark.asyncio
    async def test_execute_success_with_custom_limit(
        self, test_db_session: AsyncSession
    ) -> None:
        """正常系: カスタムlimitでランダムな画像を取得できる."""
        # Arrange - DBに10件のテストデータを挿入
        await insert_test_lgtm_images(test_db_session, count=10)

        repository = LgtmImageRepository(test_db_session)
        custom_limit = 3
        base_url = "example.com"
        random.seed(100)

        # Act
        result = await ExtractRandomLgtmImagesUsecase.execute(
            repository=repository,
            base_url=base_url,
            limit=custom_limit,
        )

        # Assert
        assert len(result) == custom_limit
        assert all(isinstance(image, dict) for image in result)
        assert all("id" in image and "url" in image for image in result)

    @pytest.mark.asyncio
    async def test_execute_raises_err_record_count_when_insufficient_images(
        self, test_db_session: AsyncSession
    ) -> None:
        """異常系: 利用可能な画像数が不足している場合にErrRecordCountが発生する."""
        # Arrange - DBに10件のテストデータを挿入
        await insert_test_lgtm_images(test_db_session, count=10)

        repository = LgtmImageRepository(test_db_session)
        base_url = "example.com"
        limit = 20  # 10個しかないのに20個要求

        # Act & Assert
        with pytest.raises(ErrRecordCount):
            await ExtractRandomLgtmImagesUsecase.execute(
                repository=repository,
                base_url=base_url,
                limit=limit,
            )

    @pytest.mark.asyncio
    async def test_execute_converts_objects_to_entities_correctly(
        self, test_db_session: AsyncSession
    ) -> None:
        """正常系: LgtmImageObjectがLgtmImageに正しく変換される."""
        # Arrange - DBに10件のテストデータを挿入
        await insert_test_lgtm_images(test_db_session, count=10)

        repository = LgtmImageRepository(test_db_session)
        base_url = "cdn.example.com"
        limit = 5
        random.seed(100)

        # Act
        result = await ExtractRandomLgtmImagesUsecase.execute(
            repository=repository,
            base_url=base_url,
            limit=limit,
        )

        # Assert
        assert len(result) == limit
        for image in result:
            # URLの形式が正しいか確認
            assert image["url"].startswith(f"https://{base_url}")
            assert "/" in image["url"]  # pathが含まれている
            assert image["url"].endswith(".webp")

            # IDが文字列として正しく設定されているか確認
            assert isinstance(image["id"], str)
            assert image["id"].isdigit()

    @pytest.mark.asyncio
    async def test_execute_returns_different_results_with_different_seeds(
        self, test_db_session: AsyncSession
    ) -> None:
        """正常系: 異なるランダムシードで異なる結果が返される."""
        # Arrange - DBに10件のテストデータを挿入
        await insert_test_lgtm_images(test_db_session, count=10)

        repository = LgtmImageRepository(test_db_session)
        base_url = "example.com"
        limit = 5

        # Act - 異なるシードで2回実行
        random.seed(1)
        result1 = await ExtractRandomLgtmImagesUsecase.execute(
            repository=repository,
            base_url=base_url,
            limit=limit,
        )

        random.seed(2)
        result2 = await ExtractRandomLgtmImagesUsecase.execute(
            repository=repository,
            base_url=base_url,
            limit=limit,
        )

        # Assert - 結果が異なることを確認
        result1_ids = {img["id"] for img in result1}
        result2_ids = {img["id"] for img in result2}
        assert result1_ids != result2_ids
