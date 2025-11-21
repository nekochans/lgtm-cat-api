# 絶対厳守：編集前に必ずAI実装ルールを読む

import base64
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.lgtm_image_repository import LgtmImageRepository
from presentation.controller.lgtm_image_controller import LgtmImageController
from presentation.controller.lgtm_image_request import (
    LgtmImageCreateFromUrlRequest,
    LgtmImageCreateRequest,
    LgtmImageSearchByImageRequest,
)
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
        assert "lgtmImages" in content
        assert isinstance(content["lgtmImages"], list)
        assert len(content["lgtmImages"]) > 0

        # Assert - デフォルトのlimit(9)で正しい数の画像を返すことを検証
        assert len(content["lgtmImages"]) == 9

        # Assert - 各アイテムの構造とドメインエンティティの変換を検証
        for item in content["lgtmImages"]:
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
            assert "lgtmImages" in content
            assert len(content["lgtmImages"]) > 0
            for item in content["lgtmImages"]:
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
        assert "lgtmImages" in content
        assert isinstance(content["lgtmImages"], list)
        assert len(content["lgtmImages"]) > 0

        # Assert - デフォルトのlimit(9)で正しい数の画像を返すことを検証
        assert len(content["lgtmImages"]) == 9

        # Assert - 各アイテムの構造を検証
        for item in content["lgtmImages"]:
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
            assert "lgtmImages" in content
            assert len(content["lgtmImages"]) > 0
            for item in content["lgtmImages"]:
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

    @pytest.mark.asyncio
    @pytest.mark.parametrize("extension", [".png", ".jpg", ".jpeg"])
    async def test_create_success_with_valid_extensions(self, extension: str) -> None:
        """正常系: 有効な拡張子で正しく画像を作成できる."""
        # Arrange
        object_storage_repository = Mock()
        object_storage_repository.upload = AsyncMock()

        base_url = "storage.example.com"

        test_image_data = b"test image"
        encoded_image = base64.b64encode(test_image_data).decode("utf-8")

        request_body = LgtmImageCreateRequest(
            image=encoded_image, imageExtension=extension
        )

        # Act
        with patch(
            "usecase.create_lgtm_image_usecase.generate_lgtm_image_name",
            return_value="test-uuid-789",
        ):
            result = await LgtmImageController.create(
                object_storage_repository=object_storage_repository,
                base_url=base_url,
                request_body=request_body,
            )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 202

        content = json.loads(bytes(result.body))
        assert "imageUrl" in content
        assert base_url in content["imageUrl"]
        assert "test-uuid-789" in content["imageUrl"]
        assert content["imageUrl"].endswith(".webp")

        # リポジトリのuploadが呼ばれたことを確認
        object_storage_repository.upload.assert_called_once()

    def test_create_raises_error_with_invalid_extension(self) -> None:
        """異常系: 無効な拡張子でPydantic ValidationErrorが発生する."""
        # Arrange
        test_image_data = b"test gif image"
        encoded_image = base64.b64encode(test_image_data).decode("utf-8")

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            LgtmImageCreateRequest(image=encoded_image, imageExtension=".gif")

        # バリデーションエラーの詳細を確認
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("imageExtension",)
        assert "Invalid image extension" in str(errors[0]["msg"])

    @pytest.mark.asyncio
    async def test_create_raises_error_with_object_storage_failure(self) -> None:
        """異常系: アップロード失敗で500エラーを返す."""
        # Arrange
        object_storage_repository = Mock()
        # エラーをシミュレート
        object_storage_repository.upload = AsyncMock(
            side_effect=Exception("object strage upload failed")
        )

        base_url = "example.com"

        test_image_data = b"test image"
        encoded_image = base64.b64encode(test_image_data).decode("utf-8")

        request_body = LgtmImageCreateRequest(
            image=encoded_image, imageExtension=".png"
        )

        # Act
        with patch(
            "usecase.create_lgtm_image_usecase.generate_lgtm_image_name",
            return_value="test-uuid-error",
        ):
            result = await LgtmImageController.create(
                object_storage_repository=object_storage_repository,
                base_url=base_url,
                request_body=request_body,
            )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500

        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "Internal server error" in content["error"]

    @pytest.mark.asyncio
    async def test_create_from_url_success(self) -> None:
        """正常系: 許可されたURLから画像を取得してアップロードに成功する."""
        # Arrange
        image_url = "https://example.com/image.png"
        base_url = "lgtm-images.lgtmeow.com"
        expected_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        mock_image_fetch_repo = AsyncMock()
        mock_image_fetch_repo.fetch_image = AsyncMock(
            return_value={"data": expected_data, "mime_type": "image/png"}
        )

        mock_storage_repo = AsyncMock()
        mock_storage_repo.upload = AsyncMock()

        request_body = LgtmImageCreateFromUrlRequest(imageUrl=image_url)

        # Act
        with patch(
            "usecase.create_lgtm_image_from_url_usecase.generate_lgtm_image_name",
            return_value="test-uuid-url",
        ):
            result = await LgtmImageController.create_from_url(
                image_fetch_repository=mock_image_fetch_repo,
                object_storage_repository=mock_storage_repo,
                base_url=base_url,
                request_body=request_body,
            )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 202

        content = json.loads(bytes(result.body))
        assert "imageUrl" in content
        assert base_url in content["imageUrl"]
        assert "test-uuid-url" in content["imageUrl"]
        assert content["imageUrl"].endswith(".webp")

        mock_image_fetch_repo.fetch_image.assert_called_once_with(image_url)
        mock_storage_repo.upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_from_url_invalid_url_error(self) -> None:
        """異常系: 無効なURLの場合、400エラーを返す."""
        # Arrange
        image_url = "https://localhost/image.png"
        base_url = "lgtm-images.lgtmeow.com"

        mock_image_fetch_repo = AsyncMock()
        from domain.lgtm_image_errors import ErrInvalidUrl

        mock_image_fetch_repo.fetch_image = AsyncMock(
            side_effect=ErrInvalidUrl("Invalid URL")
        )

        mock_storage_repo = AsyncMock()

        request_body = LgtmImageCreateFromUrlRequest(imageUrl=image_url)

        # Act
        result = await LgtmImageController.create_from_url(
            image_fetch_repository=mock_image_fetch_repo,
            object_storage_repository=mock_storage_repo,
            base_url=base_url,
            request_body=request_body,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 400

        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "Invalid URL provided" in content["error"]

        mock_storage_repo.upload.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_from_url_not_accessible_error(self) -> None:
        """異常系: URLにアクセスできない場合、400エラーを返す."""
        # Arrange
        image_url = "https://example.com/not-found.png"
        base_url = "lgtm-images.lgtmeow.com"

        mock_image_fetch_repo = AsyncMock()
        from domain.lgtm_image_errors import ErrUrlNotAccessible

        mock_image_fetch_repo.fetch_image = AsyncMock(
            side_effect=ErrUrlNotAccessible("URL not found")
        )

        mock_storage_repo = AsyncMock()

        request_body = LgtmImageCreateFromUrlRequest(imageUrl=image_url)

        # Act
        result = await LgtmImageController.create_from_url(
            image_fetch_repository=mock_image_fetch_repo,
            object_storage_repository=mock_storage_repo,
            base_url=base_url,
            request_body=request_body,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 400

        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "URL not accessible" in content["error"]

        mock_storage_repo.upload.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_from_url_fetch_failed_error(self) -> None:
        """異常系: 画像取得失敗の場合、422エラーを返す."""
        # Arrange
        image_url = "https://example.com/image.png"
        base_url = "lgtm-images.lgtmeow.com"

        mock_image_fetch_repo = AsyncMock()
        from domain.lgtm_image_errors import ErrImageFetchFailed

        mock_image_fetch_repo.fetch_image = AsyncMock(
            side_effect=ErrImageFetchFailed("Failed to fetch")
        )

        mock_storage_repo = AsyncMock()

        request_body = LgtmImageCreateFromUrlRequest(imageUrl=image_url)

        # Act
        result = await LgtmImageController.create_from_url(
            image_fetch_repository=mock_image_fetch_repo,
            object_storage_repository=mock_storage_repo,
            base_url=base_url,
            request_body=request_body,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 422

        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "Failed to fetch image from URL" in content["error"]

        mock_storage_repo.upload.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_from_url_invalid_extension_error(self) -> None:
        """異常系: サポートされていない画像形式の場合、422エラーを返す."""
        # Arrange
        image_url = "https://example.com/image.gif"
        base_url = "lgtm-images.lgtmeow.com"

        # GIFのマジックナンバー
        gif_data = b"GIF89a" + b"\x00" * 100

        mock_image_fetch_repo = AsyncMock()
        mock_image_fetch_repo.fetch_image = AsyncMock(
            return_value={"data": gif_data, "mime_type": "image/gif"}
        )

        mock_storage_repo = AsyncMock()

        request_body = LgtmImageCreateFromUrlRequest(imageUrl=image_url)

        # Act
        result = await LgtmImageController.create_from_url(
            image_fetch_repository=mock_image_fetch_repo,
            object_storage_repository=mock_storage_repo,
            base_url=base_url,
            request_body=request_body,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 422

        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "Invalid image extension or unsupported format" in content["error"]

        mock_storage_repo.upload.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_from_url_general_exception_error(self) -> None:
        """異常系: 予期しないエラーの場合、500エラーを返す."""
        # Arrange
        image_url = "https://example.com/image.png"
        base_url = "lgtm-images.lgtmeow.com"

        mock_image_fetch_repo = AsyncMock()
        mock_image_fetch_repo.fetch_image = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        mock_storage_repo = AsyncMock()

        request_body = LgtmImageCreateFromUrlRequest(imageUrl=image_url)

        # Act
        result = await LgtmImageController.create_from_url(
            image_fetch_repository=mock_image_fetch_repo,
            object_storage_repository=mock_storage_repo,
            base_url=base_url,
            request_body=request_body,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500

        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "Internal server error" in content["error"]

        mock_storage_repo.upload.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_by_text_success_with_results(self) -> None:
        """正常系: 検索クエリで複数の結果が返る."""
        # Arrange
        query = "cat"
        mock_repository = AsyncMock()
        mock_repository.search_by_text = AsyncMock(
            return_value=[
                {
                    "id": "1",
                    "url": "https://example.com/lgtm1.webp",
                    "similarity_score": 0.9,
                },
                {
                    "id": "2",
                    "url": "https://example.com/lgtm2.webp",
                    "similarity_score": 0.8,
                },
                {
                    "id": "3",
                    "url": "https://example.com/lgtm3.webp",
                    "similarity_score": 0.7,
                },
            ]
        )

        # Act
        result = await LgtmImageController.search_by_text(
            repository=mock_repository,
            query=query,
        )

        # Assert - JSONResponseを返すことを検証
        assert isinstance(result, JSONResponse)
        assert result.status_code == 200

        # Assert - レスポンス構造を検証
        content = json.loads(bytes(result.body))
        assert isinstance(content, dict)
        assert "lgtmImages" in content
        assert isinstance(content["lgtmImages"], list)
        assert len(content["lgtmImages"]) == 3

        # Assert - 各アイテムの構造を検証
        for item in content["lgtmImages"]:
            assert "id" in item
            assert "url" in item
            assert "similarityScore" in item
            assert isinstance(item["id"], str)
            assert isinstance(item["url"], str)
            assert isinstance(item["similarityScore"], float)

        # Assert - モックが正しく呼ばれたことを検証
        mock_repository.search_by_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_by_text_success_with_empty_results(self) -> None:
        """正常系: 検索結果が0件の場合、空の配列を返す."""
        # Arrange
        query = "nonexistent"
        mock_repository = AsyncMock()
        mock_repository.search_by_text = AsyncMock(return_value=[])

        # Act
        result = await LgtmImageController.search_by_text(
            repository=mock_repository,
            query=query,
        )

        # Assert - JSONResponseを返すことを検証
        assert isinstance(result, JSONResponse)
        assert result.status_code == 200

        # Assert - レスポンス構造を検証
        content = json.loads(bytes(result.body))
        assert isinstance(content, dict)
        assert "lgtmImages" in content
        assert isinstance(content["lgtmImages"], list)
        assert len(content["lgtmImages"]) == 0

        # Assert - モックが正しく呼ばれたことを検証
        mock_repository.search_by_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_by_text_raises_error_with_invalid_query(self) -> None:
        """異常系: ErrInvalidSearchQueryが発生した場合、400エラーを返す."""
        # Arrange
        query = ""
        mock_repository = AsyncMock()
        mock_repository.search_by_text = AsyncMock(return_value=[])

        # Act
        result = await LgtmImageController.search_by_text(
            repository=mock_repository,
            query=query,
        )

        # Assert - JSONResponseを返すことを検証
        assert isinstance(result, JSONResponse)
        assert result.status_code == 400

        # Assert - エラーメッセージが含まれることを検証
        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "Search query cannot be empty" in content["error"]

        # Assert - 無効なクエリの場合、リポジトリが呼ばれないことを検証
        mock_repository.search_by_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_by_text_raises_error_with_unexpected_exception(self) -> None:
        """異常系: 予期しないエラーの場合、500エラーを返す."""
        # Arrange
        query = "cat"
        mock_repository = AsyncMock()
        mock_repository.search_by_text = AsyncMock(
            side_effect=Exception("Unexpected database error")
        )

        # Act
        result = await LgtmImageController.search_by_text(
            repository=mock_repository,
            query=query,
        )

        # Assert - JSONResponseを返すことを検証
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500

        # Assert - エラーメッセージが含まれることを検証
        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "Internal server error" in content["error"]

        # Assert - モックが正しく呼ばれたことを検証
        mock_repository.search_by_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_by_image_success_with_results(self) -> None:
        """正常系: 類似画像検索で複数の結果が返る."""
        # Arrange
        mock_request = LgtmImageSearchByImageRequest(
            image="base64encodedimagedata", imageExtension=".png"
        )
        mock_repository = AsyncMock()
        mock_repository.search_by_image = AsyncMock(
            return_value=[
                {
                    "id": "1",
                    "url": "https://example.com/lgtm1.webp",
                    "similarity_score": 0.95,
                },
                {
                    "id": "2",
                    "url": "https://example.com/lgtm2.webp",
                    "similarity_score": 0.87,
                },
                {
                    "id": "3",
                    "url": "https://example.com/lgtm3.webp",
                    "similarity_score": 0.75,
                },
            ]
        )

        # Act
        result = await LgtmImageController.search_by_image(
            repository=mock_repository,
            request=mock_request,
        )

        # Assert - JSONResponseを返すことを検証
        assert isinstance(result, JSONResponse)
        assert result.status_code == 200

        # Assert - レスポンス構造を検証
        content = json.loads(bytes(result.body))
        assert isinstance(content, dict)
        assert "lgtmImages" in content
        assert isinstance(content["lgtmImages"], list)
        assert len(content["lgtmImages"]) == 3

        # Assert - 各アイテムの構造を検証（類似度スコア付き）
        for item in content["lgtmImages"]:
            assert "id" in item
            assert "url" in item
            assert "similarityScore" in item
            assert isinstance(item["id"], str)
            assert isinstance(item["url"], str)
            assert isinstance(item["similarityScore"], (int, float))

        # Assert - モックが正しく呼ばれたことを検証
        mock_repository.search_by_image.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_by_image_success_with_empty_results(self) -> None:
        """正常系: 類似画像検索で結果が0件の場合."""
        # Arrange
        mock_request = LgtmImageSearchByImageRequest(
            image="base64encodedimagedata", imageExtension=".jpg"
        )
        mock_repository = AsyncMock()
        mock_repository.search_by_image = AsyncMock(return_value=[])

        # Act
        result = await LgtmImageController.search_by_image(
            repository=mock_repository,
            request=mock_request,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 200

        content = json.loads(bytes(result.body))
        assert content == {"lgtmImages": []}

        mock_repository.search_by_image.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_by_image_raises_error_with_unexpected_exception(
        self,
    ) -> None:
        """異常系: 予期しないエラーが発生した場合、500エラーを返す."""
        # Arrange
        mock_request = LgtmImageSearchByImageRequest(
            image="base64encodedimagedata", imageExtension=".png"
        )
        mock_repository = AsyncMock()
        mock_repository.search_by_image = AsyncMock(
            side_effect=Exception("Unexpected database error")
        )

        # Act
        result = await LgtmImageController.search_by_image(
            repository=mock_repository,
            request=mock_request,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500

        content = json.loads(bytes(result.body))
        assert "error" in content
        assert content["error"] == "Internal server error"

        mock_repository.search_by_image.assert_called_once()
