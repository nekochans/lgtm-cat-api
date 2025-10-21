# 絶対厳守：編集前に必ずAI実装ルールを読む

import json

import pytest
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.lgtm_image_repository import LgtmImageRepository
from src.presentation.controller.lgtm_image_controller import LgtmImageController
from tests.fixtures.test_data_helpers import insert_test_lgtm_images


class TestLgtmImageController:
    @pytest.mark.asyncio
    async def test_exec_success_with_default_parameters(
        self, test_db_session: AsyncSession
    ) -> None:
        """正常系（デフォルトのパラメータのみで実行）: レスポンスの構造、データ形式、件数を検証."""
        # Arrange - DBに20件のテストデータを挿入
        await insert_test_lgtm_images(test_db_session, count=20)

        repository = LgtmImageRepository(test_db_session)
        base_url = "cdn.example.com"

        # Act
        result = await LgtmImageController.exec(
            repository=repository,
            base_url=base_url,
        )

        # Assert - JSONResponseを返すことを検証
        assert isinstance(result, JSONResponse)
        assert result.status_code == 200

        # Assert - レスポンス構造を検証
        content = json.loads(bytes(result.body))
        assert isinstance(content, dict)
        assert "LgtmImages" in content
        assert isinstance(content["LgtmImages"], list)
        assert len(content["LgtmImages"]) > 0

        # Assert - デフォルトのlimit(9)で正しい数の画像を返すことを検証
        assert len(content["LgtmImages"]) == 9

        # Assert - 各アイテムの構造とドメインエンティティの変換を検証
        for item in content["LgtmImages"]:
            assert "id" in item
            assert "url" in item
            assert isinstance(item["id"], str)
            assert isinstance(item["url"], str)
            # IDは数字の文字列
            assert item["id"].isdigit()
            # URLは指定されたbase_urlで始まる
            assert item["url"].startswith(f"https://{base_url}")
            # URLにはパスが含まれる
            assert "/" in item["url"]
            # 拡張子が含まれる
            assert item["url"].endswith(".webp")

    @pytest.mark.asyncio
    async def test_exec_with_different_base_urls(
        self, test_db_session: AsyncSession
    ) -> None:
        """正常系: 異なるbase_urlで正しく動作する."""
        # Arrange - DBに20件のテストデータを挿入
        await insert_test_lgtm_images(test_db_session, count=20)

        repository = LgtmImageRepository(test_db_session)
        base_urls = [
            "example.com",
            "cdn.example.com",
            "storage.example.com",
        ]

        for base_url in base_urls:
            # Act
            result = await LgtmImageController.exec(
                repository=repository,
                base_url=base_url,
            )

            # Assert
            assert isinstance(result, JSONResponse)
            content = json.loads(bytes(result.body))
            assert "LgtmImages" in content
            assert len(content["LgtmImages"]) > 0
            for item in content["LgtmImages"]:
                assert item["url"].startswith(f"https://{base_url}")

    @pytest.mark.asyncio
    async def test_exec_raises_error_when_insufficient_records(
        self, test_db_session: AsyncSession
    ) -> None:
        """異常系: レコード数が不足している場合に404を返す."""
        # Arrange - DBに5件のデータを挿入（デフォルトのlimitは9件なので不足）
        await insert_test_lgtm_images(test_db_session, count=5)

        repository = LgtmImageRepository(test_db_session)
        base_url = "example.com"

        # Act
        result = await LgtmImageController.exec(
            repository=repository,
            base_url=base_url,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 404
        content = json.loads(bytes(result.body))
        assert "error" in content
        assert content["error"] == "Insufficient LGTM images available"

    @pytest.mark.asyncio
    async def test_exec_raises_error_when_no_records(
        self, test_db_session: AsyncSession
    ) -> None:
        """異常系: レコードが0件の場合に404を返す."""
        # Arrange - DBにデータを挿入しない（0件）
        repository = LgtmImageRepository(test_db_session)
        base_url = "example.com"

        # Act
        result = await LgtmImageController.exec(
            repository=repository,
            base_url=base_url,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 404
        content = json.loads(bytes(result.body))
        assert "error" in content
        assert content["error"] == "Insufficient LGTM images available"

    @pytest.mark.asyncio
    async def test_exec_propagates_repository_errors(
        self, test_db_session: AsyncSession
    ) -> None:
        """異常系: リポジトリのエラーで500を返す."""
        # Arrange - lgtm_imagesテーブルを削除してDBエラーを発生させる
        await test_db_session.execute(text("DROP TABLE IF EXISTS lgtm_images"))
        await test_db_session.commit()

        repository = LgtmImageRepository(test_db_session)
        base_url = "example.com"

        # Act
        result = await LgtmImageController.exec(
            repository=repository,
            base_url=base_url,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500
        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "Internal server error" in content["error"]

    @pytest.mark.asyncio
    async def test_exec_recently_created_success(
        self, test_db_session: AsyncSession
    ) -> None:
        """正常系: 最近作成された画像を正しく取得できる."""
        # Arrange - DBに20件のテストデータを挿入
        await insert_test_lgtm_images(test_db_session, count=20)

        repository = LgtmImageRepository(test_db_session)
        base_url = "cdn.example.com"

        # Act
        result = await LgtmImageController.exec_recently_created(
            repository=repository,
            base_url=base_url,
        )

        # Assert - JSONResponseを返すことを検証
        assert isinstance(result, JSONResponse)
        assert result.status_code == 200

        # Assert - レスポンス構造を検証
        content = json.loads(bytes(result.body))
        assert isinstance(content, dict)
        assert "LgtmImages" in content
        assert isinstance(content["LgtmImages"], list)
        assert len(content["LgtmImages"]) > 0

        # Assert - デフォルトのlimit(9)で正しい数の画像を返すことを検証
        assert len(content["LgtmImages"]) == 9

        # Assert - 各アイテムの構造を検証
        for item in content["LgtmImages"]:
            assert "id" in item
            assert "url" in item
            assert isinstance(item["id"], str)
            assert isinstance(item["url"], str)
            # IDは数字の文字列
            assert item["id"].isdigit()
            # URLは指定されたbase_urlで始まる
            assert item["url"].startswith(f"https://{base_url}")
            # URLにはパスが含まれる
            assert "/" in item["url"]
            # 拡張子が含まれる
            assert item["url"].endswith(".webp")

    @pytest.mark.asyncio
    async def test_exec_recently_created_with_different_base_urls(
        self, test_db_session: AsyncSession
    ) -> None:
        """正常系: 異なるbase_urlで正しく動作する."""
        # Arrange - DBに20件のテストデータを挿入
        await insert_test_lgtm_images(test_db_session, count=20)

        repository = LgtmImageRepository(test_db_session)
        base_urls = [
            "example.com",
            "cdn.example.com",
            "storage.example.com",
        ]

        for base_url in base_urls:
            # Act
            result = await LgtmImageController.exec_recently_created(
                repository=repository,
                base_url=base_url,
            )

            # Assert
            assert isinstance(result, JSONResponse)
            content = json.loads(bytes(result.body))
            assert "LgtmImages" in content
            assert len(content["LgtmImages"]) > 0
            for item in content["LgtmImages"]:
                assert item["url"].startswith(f"https://{base_url}")

    @pytest.mark.asyncio
    async def test_exec_recently_created_raises_error_when_insufficient_records(
        self, test_db_session: AsyncSession
    ) -> None:
        """異常系: レコード数が不足している場合に404を返す."""
        # Arrange - DBに5件のデータを挿入（デフォルトのlimitは9件なので不足）
        await insert_test_lgtm_images(test_db_session, count=5)

        repository = LgtmImageRepository(test_db_session)
        base_url = "example.com"

        # Act
        result = await LgtmImageController.exec_recently_created(
            repository=repository,
            base_url=base_url,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 404
        content = json.loads(bytes(result.body))
        assert "error" in content
        assert content["error"] == "Insufficient LGTM images available"

    @pytest.mark.asyncio
    async def test_exec_recently_created_raises_error_when_no_records(
        self, test_db_session: AsyncSession
    ) -> None:
        """異常系: レコードが0件の場合に404を返す."""
        # Arrange - DBにデータを挿入しない
        repository = LgtmImageRepository(test_db_session)
        base_url = "example.com"

        # Act
        result = await LgtmImageController.exec_recently_created(
            repository=repository,
            base_url=base_url,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 404
        content = json.loads(bytes(result.body))
        assert "error" in content
        assert content["error"] == "Insufficient LGTM images available"

    @pytest.mark.asyncio
    async def test_exec_recently_created_propagates_repository_errors(
        self, test_db_session: AsyncSession
    ) -> None:
        """異常系: リポジトリのエラーで500を返す."""
        # Arrange - lgtm_imagesテーブルを削除してDBエラーを発生させる
        await test_db_session.execute(text("DROP TABLE IF EXISTS lgtm_images"))
        await test_db_session.commit()

        repository = LgtmImageRepository(test_db_session)
        base_url = "example.com"

        # Act
        result = await LgtmImageController.exec_recently_created(
            repository=repository,
            base_url=base_url,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500
        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "Internal server error" in content["error"]
