# 絶対厳守：編集前に必ずAI実装ルールを読む

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.responses import JSONResponse

from domain.lgtm_image_errors import (
    ErrImageFetchFailed,
    ErrInvalidImageExtension,
    ErrInvalidSearchQuery,
    ErrInvalidUrl,
    ErrUrlNotAccessible,
)
from presentation.controller.lgtm_image_controller import LgtmImageController
from presentation.controller.lgtm_image_request import (
    LgtmImageSearchByImageFromUrlRequest,
    LgtmImageSearchByImageRequest,
)


class TestLgtmImageControllerSearchByText:
    """LgtmImageController.search_by_text() のテスト.

    外部サービス（ベクトル検索サービス）に依存するため、
    UseCaseクラスをpatchしてテストする。
    """

    @pytest.mark.asyncio
    @patch(
        "presentation.controller.lgtm_image_controller.SearchLgtmImagesByTextUsecase"
    )
    async def test_search_by_text_success_with_results(
        self, mock_usecase_class: Mock
    ) -> None:
        """正常系: 検索クエリで複数の結果が返る."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(
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

        mock_repository = AsyncMock()
        query = "cat"

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

        # Assert - UseCaseが正しく呼ばれたことを検証
        mock_usecase_class.execute.assert_called_once_with(mock_repository, query)

    @pytest.mark.asyncio
    @patch(
        "presentation.controller.lgtm_image_controller.SearchLgtmImagesByTextUsecase"
    )
    async def test_search_by_text_success_with_empty_results(
        self, mock_usecase_class: Mock
    ) -> None:
        """正常系: 検索結果が0件の場合、空の配列を返す."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(return_value=[])

        mock_repository = AsyncMock()
        query = "nonexistent"

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

        # Assert - UseCaseが正しく呼ばれたことを検証
        mock_usecase_class.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "presentation.controller.lgtm_image_controller.SearchLgtmImagesByTextUsecase"
    )
    async def test_search_by_text_raises_error_with_invalid_query(
        self, mock_usecase_class: Mock
    ) -> None:
        """異常系: ErrInvalidSearchQueryが発生した場合、400エラーを返す."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(
            side_effect=ErrInvalidSearchQuery("Search query cannot be empty")
        )

        mock_repository = AsyncMock()
        query = ""

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

    @pytest.mark.asyncio
    @patch(
        "presentation.controller.lgtm_image_controller.SearchLgtmImagesByTextUsecase"
    )
    async def test_search_by_text_raises_error_with_unexpected_exception(
        self, mock_usecase_class: Mock
    ) -> None:
        """異常系: 予期しないエラーの場合、500エラーを返す."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(
            side_effect=Exception("Unexpected database error")
        )

        mock_repository = AsyncMock()
        query = "cat"

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


class TestLgtmImageControllerSearchByImage:
    """LgtmImageController.search_by_image() のテスト.

    外部サービス（ベクトル検索サービス）に依存するため、
    UseCaseクラスをpatchしてテストする。
    """

    @pytest.mark.asyncio
    @patch(
        "presentation.controller.lgtm_image_controller.SearchLgtmImagesByImageUsecase"
    )
    async def test_search_by_image_success_with_results(
        self, mock_usecase_class: Mock
    ) -> None:
        """正常系: 類似画像検索で複数の結果が返る."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(
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

        mock_repository = AsyncMock()
        mock_request = LgtmImageSearchByImageRequest(
            image="base64encodedimagedata", imageExtension=".png"
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

        # Assert - UseCaseが正しく呼ばれたことを検証
        mock_usecase_class.execute.assert_called_once_with(
            mock_repository, "base64encodedimagedata", ".png"
        )

    @pytest.mark.asyncio
    @patch(
        "presentation.controller.lgtm_image_controller.SearchLgtmImagesByImageUsecase"
    )
    async def test_search_by_image_success_with_empty_results(
        self, mock_usecase_class: Mock
    ) -> None:
        """正常系: 類似画像検索で結果が0件の場合."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(return_value=[])

        mock_repository = AsyncMock()
        mock_request = LgtmImageSearchByImageRequest(
            image="base64encodedimagedata", imageExtension=".jpg"
        )

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

        mock_usecase_class.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "presentation.controller.lgtm_image_controller.SearchLgtmImagesByImageUsecase"
    )
    async def test_search_by_image_raises_error_with_unexpected_exception(
        self, mock_usecase_class: Mock
    ) -> None:
        """異常系: 予期しないエラーが発生した場合、500エラーを返す."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(
            side_effect=Exception("Unexpected database error")
        )

        mock_repository = AsyncMock()
        mock_request = LgtmImageSearchByImageRequest(
            image="base64encodedimagedata", imageExtension=".png"
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


class TestLgtmImageControllerSearchByImageFromUrl:
    """LgtmImageController.search_by_image_from_url() のテスト.

    外部サービス（画像取得、ベクトル検索）に依存するため、
    UseCaseクラスをpatchしてテストする。
    """

    @pytest.mark.asyncio
    @patch(
        "presentation.controller.lgtm_image_controller.SearchLgtmImagesByImageFromUrlUsecase"
    )
    async def test_search_by_image_from_url_success(
        self, mock_usecase_class: Mock
    ) -> None:
        """正常系: 署名付きURLから画像を取得して検索に成功する."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(
            return_value=[
                {
                    "id": "1",
                    "url": "https://lgtm-images.lgtmeow.com/image1.webp",
                    "similarity_score": 0.95,
                },
                {
                    "id": "2",
                    "url": "https://lgtm-images.lgtmeow.com/image2.webp",
                    "similarity_score": 0.87,
                },
            ]
        )

        image_url = "https://example.com/image.png"
        mock_image_fetch_repo = AsyncMock()
        mock_search_repo = AsyncMock()
        request_body = LgtmImageSearchByImageFromUrlRequest(imageUrl=image_url)

        # Act
        result = await LgtmImageController.search_by_image_from_url(
            image_fetch_repository=mock_image_fetch_repo,
            repository=mock_search_repo,
            request=request_body,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 200

        content = json.loads(bytes(result.body))
        assert "lgtmImages" in content
        assert len(content["lgtmImages"]) == 2
        assert content["lgtmImages"][0]["id"] == "1"
        assert content["lgtmImages"][0]["similarityScore"] == 0.95
        assert content["lgtmImages"][1]["id"] == "2"
        assert content["lgtmImages"][1]["similarityScore"] == 0.87

        mock_usecase_class.execute.assert_called_once_with(
            image_fetch_repository=mock_image_fetch_repo,
            search_repository=mock_search_repo,
            image_url=image_url,
        )

    @pytest.mark.asyncio
    @patch(
        "presentation.controller.lgtm_image_controller.SearchLgtmImagesByImageFromUrlUsecase"
    )
    async def test_search_by_image_from_url_invalid_url(
        self, mock_usecase_class: Mock
    ) -> None:
        """異常系: 無効なURLの場合、400エラーを返す."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(side_effect=ErrInvalidUrl("Invalid URL"))

        image_url = "https://localhost/image.png"
        mock_image_fetch_repo = AsyncMock()
        mock_search_repo = AsyncMock()
        request_body = LgtmImageSearchByImageFromUrlRequest(imageUrl=image_url)

        # Act
        result = await LgtmImageController.search_by_image_from_url(
            image_fetch_repository=mock_image_fetch_repo,
            repository=mock_search_repo,
            request=request_body,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 400

        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "Invalid URL provided" in content["error"]

    @pytest.mark.asyncio
    @patch(
        "presentation.controller.lgtm_image_controller.SearchLgtmImagesByImageFromUrlUsecase"
    )
    async def test_search_by_image_from_url_url_not_accessible(
        self, mock_usecase_class: Mock
    ) -> None:
        """異常系: URLにアクセスできない場合、400エラーを返す."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(
            side_effect=ErrUrlNotAccessible("URL not found")
        )

        image_url = "https://example.com/not-found.png"
        mock_image_fetch_repo = AsyncMock()
        mock_search_repo = AsyncMock()
        request_body = LgtmImageSearchByImageFromUrlRequest(imageUrl=image_url)

        # Act
        result = await LgtmImageController.search_by_image_from_url(
            image_fetch_repository=mock_image_fetch_repo,
            repository=mock_search_repo,
            request=request_body,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 400

        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "URL not accessible" in content["error"]

    @pytest.mark.asyncio
    @patch(
        "presentation.controller.lgtm_image_controller.SearchLgtmImagesByImageFromUrlUsecase"
    )
    async def test_search_by_image_from_url_fetch_failed(
        self, mock_usecase_class: Mock
    ) -> None:
        """異常系: 画像取得失敗の場合、422エラーを返す."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(
            side_effect=ErrImageFetchFailed("Failed to fetch image")
        )

        image_url = "https://example.com/broken-image.png"
        mock_image_fetch_repo = AsyncMock()
        mock_search_repo = AsyncMock()
        request_body = LgtmImageSearchByImageFromUrlRequest(imageUrl=image_url)

        # Act
        result = await LgtmImageController.search_by_image_from_url(
            image_fetch_repository=mock_image_fetch_repo,
            repository=mock_search_repo,
            request=request_body,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 422

        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "Failed to fetch image from URL" in content["error"]

    @pytest.mark.asyncio
    @patch(
        "presentation.controller.lgtm_image_controller.SearchLgtmImagesByImageFromUrlUsecase"
    )
    async def test_search_by_image_from_url_invalid_extension(
        self, mock_usecase_class: Mock
    ) -> None:
        """異常系: 無効な画像形式の場合、422エラーを返す."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(
            side_effect=ErrInvalidImageExtension("Unsupported MIME type")
        )

        image_url = "https://example.com/document.pdf"
        mock_image_fetch_repo = AsyncMock()
        mock_search_repo = AsyncMock()
        request_body = LgtmImageSearchByImageFromUrlRequest(imageUrl=image_url)

        # Act
        result = await LgtmImageController.search_by_image_from_url(
            image_fetch_repository=mock_image_fetch_repo,
            repository=mock_search_repo,
            request=request_body,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 422

        content = json.loads(bytes(result.body))
        assert "error" in content
        assert "Invalid image extension or unsupported format" in content["error"]

    @pytest.mark.asyncio
    @patch(
        "presentation.controller.lgtm_image_controller.SearchLgtmImagesByImageFromUrlUsecase"
    )
    async def test_search_by_image_from_url_general_exception(
        self, mock_usecase_class: Mock
    ) -> None:
        """異常系: 予期しないエラーが発生した場合、500エラーを返す."""
        # Arrange
        mock_usecase_class.execute = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        image_url = "https://example.com/image.png"
        mock_image_fetch_repo = AsyncMock()
        mock_search_repo = AsyncMock()
        request_body = LgtmImageSearchByImageFromUrlRequest(imageUrl=image_url)

        # Act
        result = await LgtmImageController.search_by_image_from_url(
            image_fetch_repository=mock_image_fetch_repo,
            repository=mock_search_repo,
            request=request_body,
        )

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500

        content = json.loads(bytes(result.body))
        assert "error" in content
        assert content["error"] == "Internal server error"
