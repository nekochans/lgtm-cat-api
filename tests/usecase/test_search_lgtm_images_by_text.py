# 絶対厳守：編集前に必ずAI実装ルールを読む

from unittest.mock import AsyncMock

import pytest

from domain.lgtm_image_errors import ErrInvalidSearchQuery
from domain.lgtm_image_search import (
    DEFAULT_SEARCH_MAX_RESULTS,
    LgtmImageSearchResult,
    MAX_QUERY_LENGTH,
)
from usecase.search_lgtm_images_by_text import SearchLgtmImagesByTextUsecase


class TestNormalizeQueryText:
    """_normalize_query_textメソッドの単体テスト."""

    @pytest.mark.parametrize(
        "input_text,expected,description",
        [
            # Unicode正規化（NFKC）のテスト
            ("ＡＢＣ１２３", "ABC123", "全角英数字が半角に正規化される"),
            ("ｶﾀｶﾅ", "カタカナ", "半角カタカナが全角に正規化される"),
            ("か\u3099", "が", "分離された濁点が結合文字に正規化される"),
            # 空白正規化のテスト
            (
                "hello    world",
                "hello world",
                "連続する空白が単一スペースに正規化される",
            ),
            ("hello\t\nworld", "hello world", "タブと改行が単一スペースに正規化される"),
            ("hello　world", "hello world", "全角スペースが半角スペースに正規化される"),
            # トリムのテスト
            ("  hello world  ", "hello world", "前後の空白が削除される"),
            # 複合パターン
            (
                "  ｶﾀｶﾅ　　ＡＢＣ    １２３\n\ttest  ",
                "カタカナ ABC 123 test",
                "複雑な混在入力が正しく正規化される",
            ),
            ("   \t\n   ", "", "空白のみの入力は空文字列になる"),
        ],
    )
    def test_normalizes_query_text(
        self, input_text: str, expected: str, description: str
    ) -> None:
        """クエリテキストが正しく正規化される."""
        # Act
        result = SearchLgtmImagesByTextUsecase._normalize_query_text(input_text)

        # Assert
        assert result == expected, description

    def test_normalizes_dakuten_separately_to_combined_verifies_length(self) -> None:
        """分離された濁点が1文字に結合されることを長さで確認."""
        # Arrange
        query_text = "か\u3099"  # U+304B + U+3099 (基底文字 + 結合濁点)

        # Act
        result = SearchLgtmImagesByTextUsecase._normalize_query_text(query_text)

        # Assert
        assert result == "が"  # U+304C (合成済み文字)
        assert len(result) == 1  # 1文字に結合される


class TestValidateQueryText:
    """_validate_query_textメソッドの単体テスト."""

    @pytest.mark.parametrize(
        "query_text,description",
        [
            ("a", "1文字のクエリは受け入れられる"),
            ("猫の画像を検索", "有効な日本語クエリは受け入れられる"),
            ("search for cat images", "有効な英語クエリは受け入れられる"),
            (
                "a" * MAX_QUERY_LENGTH,
                f"最大文字数（{MAX_QUERY_LENGTH}文字）のクエリは受け入れられる",
            ),
            (
                "あ" * MAX_QUERY_LENGTH,
                f"日本語で{MAX_QUERY_LENGTH}文字のクエリは受け入れられる",
            ),
        ],
    )
    def test_accepts_valid_query(self, query_text: str, description: str) -> None:
        """有効なクエリが受け入れられる."""
        # Act & Assert - 例外が発生しないことを確認
        try:
            SearchLgtmImagesByTextUsecase._validate_query_text(query_text)
        except ErrInvalidSearchQuery:
            pytest.fail(f"{description}のに例外が発生した")

    @pytest.mark.parametrize(
        "query_text,expected_message",
        [
            (
                "",
                "Search query cannot be empty",
            ),
            (
                "a" * (MAX_QUERY_LENGTH + 1),
                f"Search query must be {MAX_QUERY_LENGTH} characters or less",
            ),
            (
                "あ" * (MAX_QUERY_LENGTH + 1),
                f"Search query must be {MAX_QUERY_LENGTH} characters or less",
            ),
        ],
        ids=[
            "空文字列でErrInvalidSearchQueryが発生する",
            f"{MAX_QUERY_LENGTH + 1}文字でErrInvalidSearchQueryが発生する",
            f"日本語{MAX_QUERY_LENGTH + 1}文字でErrInvalidSearchQueryが発生する",
        ],
    )
    def test_raises_invalid_search_query_for_invalid_query(
        self, query_text: str, expected_message: str
    ) -> None:
        """無効なクエリでErrInvalidSearchQueryが発生する."""
        # Act & Assert
        with pytest.raises(ErrInvalidSearchQuery, match=expected_message):
            SearchLgtmImagesByTextUsecase._validate_query_text(query_text)


class TestSearchLgtmImagesByTextUsecase:
    """SearchLgtmImagesByTextUsecaseの統合テスト.

    正規化とバリデーションの詳細テストは
    TestNormalizeQueryTextとTestValidateQueryTextで実施。
    ここでは正規化→バリデーション→リポジトリ呼び出しの
    統合的な動作を確認する。
    """

    @pytest.mark.asyncio
    async def test_execute_success_with_valid_query(self) -> None:
        """正常系: 有効なクエリテキストから画像が返る."""
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
        mock_repository.search_by_text.return_value = mock_results

        query_text = "happy cat"

        # Act
        result = await SearchLgtmImagesByTextUsecase.execute(
            repository=mock_repository,
            query_text=query_text,
        )

        # Assert
        assert len(result) == 3
        assert result == mock_results
        mock_repository.search_by_text.assert_called_once_with(
            query_text, max_results=DEFAULT_SEARCH_MAX_RESULTS
        )

    @pytest.mark.asyncio
    async def test_execute_success_with_empty_results(self) -> None:
        """正常系: 検索結果が0件の場合でも空のリストが返る."""
        # Arrange
        mock_repository = AsyncMock()
        mock_repository.search_by_text.return_value = []

        query_text = "nonexistent keyword"

        # Act
        result = await SearchLgtmImagesByTextUsecase.execute(
            repository=mock_repository,
            query_text=query_text,
        )

        # Assert
        assert len(result) == 0
        assert result == []
        mock_repository.search_by_text.assert_called_once_with(
            query_text, max_results=DEFAULT_SEARCH_MAX_RESULTS
        )

    @pytest.mark.asyncio
    async def test_execute_raises_value_error_with_empty_string(self) -> None:
        """異常系: 空文字列のクエリでErrInvalidSearchQueryが発生する."""
        # Arrange
        mock_repository = AsyncMock()
        query_text = ""

        # Act & Assert
        with pytest.raises(ErrInvalidSearchQuery, match="Search query cannot be empty"):
            await SearchLgtmImagesByTextUsecase.execute(
                repository=mock_repository,
                query_text=query_text,
            )

        # リポジトリは呼ばれないことを確認
        mock_repository.search_by_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_value_error_when_query_exceeds_max_length(
        self,
    ) -> None:
        """異常系: 文字数制限を超えるクエリでErrInvalidSearchQueryが発生する."""
        # Arrange
        mock_repository = AsyncMock()
        # MAX_QUERY_LENGTHを超えるクエリ
        query_text = "a" * (MAX_QUERY_LENGTH + 1)

        # Act & Assert
        with pytest.raises(
            ErrInvalidSearchQuery,
            match=f"Search query must be {MAX_QUERY_LENGTH} characters or less",
        ):
            await SearchLgtmImagesByTextUsecase.execute(
                repository=mock_repository,
                query_text=query_text,
            )

        # リポジトリは呼ばれないことを確認
        mock_repository.search_by_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_calls_repository_with_normalized_query(self) -> None:
        """正常系: 正規化されたクエリでリポジトリが呼ばれる."""
        # Arrange
        mock_repository = AsyncMock()
        mock_repository.search_by_text.return_value = []

        # 正規化が必要なクエリ（前後に空白、連続空白）
        query_text = "  test    query  "
        expected_normalized = "test query"

        # Act
        await SearchLgtmImagesByTextUsecase.execute(
            repository=mock_repository,
            query_text=query_text,
        )

        # Assert - 正規化されたクエリでリポジトリが呼ばれる
        mock_repository.search_by_text.assert_called_once_with(
            expected_normalized, max_results=DEFAULT_SEARCH_MAX_RESULTS
        )
