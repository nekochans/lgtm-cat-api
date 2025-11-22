# 絶対厳守:編集前に必ずAI実装ルールを読む

from unittest.mock import AsyncMock

import pytest

from domain.lgtm_image_search import (
    DEFAULT_SEARCH_MAX_RESULTS,
    LgtmImageSearchResult,
)
from usecase.search_lgtm_images_by_image import SearchLgtmImagesByImageUsecase


class TestSearchLgtmImagesByImageUsecase:
    """SearchLgtmImagesByImageUsecaseの統合テスト.

    Repository層で画像のベクトル化と検索を実行し、
    類似画像のリストが返されることを確認する。
    """

    @pytest.mark.asyncio
    async def test_execute_success_with_valid_image_data(self) -> None:
        """正常系: 有効な画像データから類似画像が返る."""
        # Arrange
        mock_repository = AsyncMock()
        mock_results: list[LgtmImageSearchResult] = [
            {
                "id": "1",
                "url": "https://example.com/image1.webp",
                "similarity_score": 0.95,
            },
            {
                "id": "2",
                "url": "https://example.com/image2.webp",
                "similarity_score": 0.87,
            },
            {
                "id": "3",
                "url": "https://example.com/image3.webp",
                "similarity_score": 0.75,
            },
        ]
        mock_repository.search_by_image.return_value = mock_results

        image_data = "iVBORw0KGgoAAAANSUhEUgAAAAUA..."
        image_extension = ".png"

        # Act
        result = await SearchLgtmImagesByImageUsecase.execute(
            repository=mock_repository,
            image_data=image_data,
            image_extension=image_extension,
        )

        # Assert
        assert len(result) == 3
        assert result == mock_results
        mock_repository.search_by_image.assert_called_once_with(
            image_data=image_data,
            image_extension=image_extension,
            max_results=DEFAULT_SEARCH_MAX_RESULTS,
        )

    @pytest.mark.asyncio
    async def test_execute_success_with_empty_results(self) -> None:
        """正常系: 検索結果が0件の場合でも空のリストが返る."""
        # Arrange
        mock_repository = AsyncMock()
        mock_repository.search_by_image.return_value = []

        image_data = "iVBORw0KGgoAAAANSUhEUgAAAAUA..."
        image_extension = ".jpg"

        # Act
        result = await SearchLgtmImagesByImageUsecase.execute(
            repository=mock_repository,
            image_data=image_data,
            image_extension=image_extension,
        )

        # Assert
        assert len(result) == 0
        assert result == []
        mock_repository.search_by_image.assert_called_once_with(
            image_data=image_data,
            image_extension=image_extension,
            max_results=DEFAULT_SEARCH_MAX_RESULTS,
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "image_extension",
        [
            ".png",
            ".jpg",
            ".jpeg",
        ],
        ids=["png", "jpg", "jpeg"],
    )
    async def test_execute_success_with_various_extensions(
        self, image_extension: str
    ) -> None:
        """正常系: 各種画像拡張子で正常に動作する."""
        # Arrange
        mock_repository = AsyncMock()
        mock_results: list[LgtmImageSearchResult] = [
            {
                "id": "1",
                "url": "https://example.com/image1.webp",
                "similarity_score": 0.90,
            }
        ]
        mock_repository.search_by_image.return_value = mock_results

        image_data = "iVBORw0KGgoAAAANSUhEUgAAAAUA..."

        # Act
        result = await SearchLgtmImagesByImageUsecase.execute(
            repository=mock_repository,
            image_data=image_data,
            image_extension=image_extension,
        )

        # Assert
        assert len(result) == 1
        assert result == mock_results
        mock_repository.search_by_image.assert_called_once_with(
            image_data=image_data,
            image_extension=image_extension,
            max_results=DEFAULT_SEARCH_MAX_RESULTS,
        )
