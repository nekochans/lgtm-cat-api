# 絶対厳守：編集前に必ずAI実装ルールを読む

import json
from unittest.mock import AsyncMock

import pytest
from fastapi.responses import JSONResponse

from src.domain.repository.lgtm_image_repository_interface import (
    LgtmImageRepositoryInterface,
)
from src.infrastructure.lgtm_image_repository import LgtmImageRepository
from src.presentation.controller.lgtm_image_controller import LgtmImageController


class TestLgtmImageController:
    @pytest.fixture
    def repository(self) -> LgtmImageRepository:
        return LgtmImageRepository()

    @pytest.mark.asyncio
    async def test_exec_success_with_default_parameters(
        self, repository: LgtmImageRepository
    ) -> None:
        """正常系（デフォルトのパラメータのみで実行）: レスポンスの構造、データ形式、件数を検証."""
        # Arrange
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
        content = json.loads(result.body)
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
        self, repository: LgtmImageRepository
    ) -> None:
        """正常系: 異なるbase_urlで正しく動作する."""
        # Arrange
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
            content = json.loads(result.body)
            assert "LgtmImages" in content
            assert len(content["LgtmImages"]) > 0
            for item in content["LgtmImages"]:
                assert item["url"].startswith(f"https://{base_url}")

    @pytest.mark.asyncio
    async def test_exec_raises_error_when_insufficient_records(self) -> None:
        """異常系: レコード数が不足している場合に404を返す."""
        # Arrange
        mock_repository = AsyncMock(spec=LgtmImageRepositoryInterface)
        # リポジトリは5件のIDしか返さないが、デフォルトのlimitは9件
        mock_repository.find_all_ids.return_value = ["1", "2", "3", "4", "5"]
        base_url = "example.com"

        # Act
        result = await LgtmImageController.exec(
            repository=mock_repository,
            base_url=base_url,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 404
        content = json.loads(result.body)
        assert "error" in content
        assert content["error"] == "Insufficient LGTM images available"

    @pytest.mark.asyncio
    async def test_exec_raises_error_when_no_records(self) -> None:
        """異常系: レコードが0件の場合に404を返す."""
        # Arrange
        mock_repository = AsyncMock(spec=LgtmImageRepositoryInterface)
        mock_repository.find_all_ids.return_value = []
        base_url = "example.com"

        # Act
        result = await LgtmImageController.exec(
            repository=mock_repository,
            base_url=base_url,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 404
        content = json.loads(result.body)
        assert "error" in content
        assert content["error"] == "Insufficient LGTM images available"

    @pytest.mark.asyncio
    async def test_exec_propagates_repository_errors(self) -> None:
        """異常系: リポジトリのエラーで500を返す."""
        # Arrange
        mock_repository = AsyncMock(spec=LgtmImageRepositoryInterface)
        mock_repository.find_all_ids.side_effect = RuntimeError(
            "Database connection failed"
        )
        base_url = "example.com"

        # Act
        result = await LgtmImageController.exec(
            repository=mock_repository,
            base_url=base_url,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500
        content = json.loads(result.body)
        assert "error" in content
        assert "Internal server error" in content["error"]
        assert "Database connection failed" in content["error"]
