# 絶対厳守：編集前に必ずAI実装ルールを読む

"""MCP用LGTM画像ルーターのテスト.

FastAPI TestClient（httpx.AsyncClient）を使用してHTTPリクエスト経由でテストする。
Routerの依存性注入（Depends）が正しく動作することを確認する。
"""

from collections.abc import Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_lgtm_images_base_url
from infrastructure.lgtm_image_repository import LgtmImageRepository
from main import app
from presentation.router.mcp_lgtm_image_router import create_lgtm_image_repository
from tests.fixtures.test_data_helpers import insert_test_lgtm_images


@pytest.fixture
def override_dependencies(
    test_db_session: AsyncSession,
) -> Generator[None, None, None]:
    """依存性オーバーライドを設定するフィクスチャ."""
    test_base_url = "cdn.example.com"

    def _get_test_repository() -> LgtmImageRepository:
        return LgtmImageRepository(test_db_session)

    def _get_test_base_url() -> str:
        return test_base_url

    app.dependency_overrides[create_lgtm_image_repository] = _get_test_repository
    app.dependency_overrides[get_lgtm_images_base_url] = _get_test_base_url

    yield

    # クリーンアップ
    app.dependency_overrides.clear()


class TestMcpLgtmImageRouterRandomImages:
    """MCP用 GET /lgtm-images エンドポイントのテスト.

    HTTPリクエスト経由で認証なしでLGTM画像を取得できることを確認する。
    Routerの依存性注入が正しく動作することを検証する。
    """

    @pytest.mark.asyncio
    async def test_get_random_lgtm_images_success(
        self,
        test_db_session: AsyncSession,
        override_dependencies: None,
    ) -> None:
        """正常系: HTTPリクエストで認証なしでランダムなLGTM画像を取得できる."""
        # Arrange - DBに20件のテストデータを挿入
        await insert_test_lgtm_images(test_db_session, count=20)

        # Act - HTTPリクエストでエンドポイントをテスト
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/mcp/lgtm-images")

        # Assert - ステータスコードを検証
        assert response.status_code == 200

        # Assert - レスポンス構造を検証
        content = response.json()
        assert isinstance(content, dict)
        assert "lgtmImages" in content
        assert isinstance(content["lgtmImages"], list)
        assert len(content["lgtmImages"]) == 9

        # Assert - 各アイテムの構造を検証
        for item in content["lgtmImages"]:
            assert "id" in item
            assert "url" in item
            assert isinstance(item["id"], str)
            assert isinstance(item["url"], str)
            assert item["url"].startswith("https://cdn.example.com")

    @pytest.mark.asyncio
    async def test_get_random_lgtm_images_returns_404_when_insufficient_records(
        self,
        test_db_session: AsyncSession,
        override_dependencies: None,
    ) -> None:
        """異常系: レコード数が不足している場合に404を返す."""
        # Arrange - DBに5件のデータを挿入（デフォルトのlimitは9件なので不足）
        await insert_test_lgtm_images(test_db_session, count=5)

        # Act - HTTPリクエストでエンドポイントをテスト
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/mcp/lgtm-images")

        # Assert
        assert response.status_code == 404
        content = response.json()
        assert "error" in content
        assert content["error"] == "Insufficient LGTM images available"


class TestMcpLgtmImageRouterRecentlyCreated:
    """MCP用 GET /lgtm-images/recently-created エンドポイントのテスト.

    HTTPリクエスト経由で認証なしで最近作成されたLGTM画像を取得できることを確認する。
    Routerの依存性注入が正しく動作することを検証する。
    """

    @pytest.mark.asyncio
    async def test_get_recently_created_lgtm_images_success(
        self,
        test_db_session: AsyncSession,
        override_dependencies: None,
    ) -> None:
        """正常系: HTTPリクエストで認証なしで最近作成されたLGTM画像を取得できる."""
        # Arrange - DBに20件のテストデータを挿入
        await insert_test_lgtm_images(test_db_session, count=20)

        # Act - HTTPリクエストでエンドポイントをテスト
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/mcp/lgtm-images/recently-created")

        # Assert - ステータスコードを検証
        assert response.status_code == 200

        # Assert - レスポンス構造を検証
        content = response.json()
        assert isinstance(content, dict)
        assert "lgtmImages" in content
        assert isinstance(content["lgtmImages"], list)
        assert len(content["lgtmImages"]) == 9

        # Assert - 各アイテムの構造を検証
        for item in content["lgtmImages"]:
            assert "id" in item
            assert "url" in item
            assert isinstance(item["id"], str)
            assert isinstance(item["url"], str)
            assert item["url"].startswith("https://cdn.example.com")

    @pytest.mark.asyncio
    async def test_get_recently_created_returns_404_when_insufficient_records(
        self,
        test_db_session: AsyncSession,
        override_dependencies: None,
    ) -> None:
        """異常系: レコード数が不足している場合に404を返す."""
        # Arrange - DBに5件のデータを挿入（デフォルトのlimitは9件なので不足）
        await insert_test_lgtm_images(test_db_session, count=5)

        # Act - HTTPリクエストでエンドポイントをテスト
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/mcp/lgtm-images/recently-created")

        # Assert
        assert response.status_code == 404
        content = response.json()
        assert "error" in content
        assert content["error"] == "Insufficient LGTM images available"
