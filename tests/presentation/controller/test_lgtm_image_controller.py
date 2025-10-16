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
    async def test_exec_success_returns_json_response(
        self, repository: LgtmImageRepository
    ) -> None:
        """正常系: JSONResponseを返す."""
        # Arrange
        base_url = "example.com"

        # Act
        result = await LgtmImageController.exec(
            repository=repository,
            base_url=base_url,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_exec_success_response_has_correct_structure(
        self, repository: LgtmImageRepository
    ) -> None:
        """正常系: レスポンスが正しい構造を持つ."""
        # Arrange
        base_url = "cdn.example.com"

        # Act
        result = await LgtmImageController.exec(
            repository=repository,
            base_url=base_url,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        content = json.loads(result.body)
        assert isinstance(content, dict)
        assert "LgtmImages" in content
        assert isinstance(content["LgtmImages"], list)
        assert len(content["LgtmImages"]) > 0

        for item in content["LgtmImages"]:
            assert "id" in item
            assert "url" in item
            assert isinstance(item["id"], str)
            assert isinstance(item["url"], str)
            assert item["url"].startswith(f"https://{base_url}")

    @pytest.mark.asyncio
    async def test_exec_success_converts_domain_entity_to_response(
        self, repository: LgtmImageRepository
    ) -> None:
        """正常系: ドメインエンティティをレスポンスモデルに変換."""
        # Arrange
        base_url = "example.com"

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

        # IDとURLが正しく設定されているか確認
        for item in content["LgtmImages"]:
            assert item["id"].isdigit()  # IDは数字の文字列
            assert "/" in item["url"]  # URLにはパスが含まれる
            assert item["url"].endswith(".webp")  # 拡張子が含まれる

    @pytest.mark.asyncio
    async def test_exec_returns_expected_number_of_items(
        self, repository: LgtmImageRepository
    ) -> None:
        """正常系: デフォルトのlimitで正しい数の画像を返す."""
        # Arrange
        base_url = "test.example.com"

        # Act
        result = await LgtmImageController.exec(
            repository=repository,
            base_url=base_url,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        content = json.loads(result.body)
        assert "LgtmImages" in content
        # デフォルトのlimit(9)で画像が返される
        assert len(content["LgtmImages"]) == 9
        assert all("id" in item and "url" in item for item in content["LgtmImages"])

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
