# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.lgtm_image_errors import (
    ErrEmbeddingGenerationFailed,
    ErrVectorDataCorrupted,
)
from infrastructure.lgtm_image_search_repository import (
    LgtmImageSearchRepository,
)


class TestLgtmImageSearchRepository:
    @pytest.mark.asyncio
    async def test_search_by_text_success(self) -> None:
        """正常にテキスト検索が実行できることを検証"""
        # モックの設定
        mock_bedrock_client = MagicMock()
        mock_s3_vector_client = MagicMock()

        # BedrockClientのモック：埋め込みベクトルを返す
        mock_bedrock_client.generate_text_embedding = AsyncMock(
            return_value=[0.1, 0.2, 0.3, 0.4, 0.5]
        )

        # S3VectorClientのモック：検索結果を返す（source_key含む）
        mock_s3_vector_client.search_similar_vectors = AsyncMock(
            return_value=[
                {
                    "key": "123",
                    "distance": 0.15,
                    "metadata": {
                        "source_key": "2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp"
                    },
                },
                {
                    "key": "456",
                    "distance": 0.25,
                    "metadata": {
                        "source_key": "2021/03/17/12/6947f291-a46e-453c-a230-0d756d7174cc.webp"
                    },
                },
            ]
        )

        base_url = "example.com"
        repository = LgtmImageSearchRepository(
            bedrock_client=mock_bedrock_client,
            s3_vector_client=mock_s3_vector_client,
            base_url=base_url,
        )

        # テスト実行
        results = await repository.search_by_text("test query", max_results=9)

        # 検証
        assert len(results) == 2

        # 1件目の検証
        assert results[0]["id"] == "123"
        assert (
            results[0]["url"]
            == "https://example.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp"
        )
        # distance=0.15 -> similarity_score=1.0/(1.0+0.15)≈0.8696
        assert results[0]["similarity_score"] == pytest.approx(1.0 / 1.15)

        # 2件目の検証
        assert results[1]["id"] == "456"
        assert (
            results[1]["url"]
            == "https://example.com/2021/03/17/12/6947f291-a46e-453c-a230-0d756d7174cc.webp"
        )
        # distance=0.25 -> similarity_score=1.0/(1.0+0.25)=0.8
        assert results[1]["similarity_score"] == pytest.approx(0.8)

        # モックメソッドの呼び出しを検証
        mock_bedrock_client.generate_text_embedding.assert_called_once_with(
            "test query"
        )
        mock_s3_vector_client.search_similar_vectors.assert_called_once_with(
            [0.1, 0.2, 0.3, 0.4, 0.5], 9
        )

    @pytest.mark.asyncio
    async def test_search_by_text_empty_result(self) -> None:
        """検索結果が空の場合を検証"""
        # モックの設定
        mock_bedrock_client = MagicMock()
        mock_s3_vector_client = MagicMock()

        mock_bedrock_client.generate_text_embedding = AsyncMock(
            return_value=[0.1, 0.2, 0.3]
        )
        mock_s3_vector_client.search_similar_vectors = AsyncMock(return_value=[])

        base_url = "https://example.com"
        repository = LgtmImageSearchRepository(
            bedrock_client=mock_bedrock_client,
            s3_vector_client=mock_s3_vector_client,
            base_url=base_url,
        )

        # テスト実行
        results = await repository.search_by_text("no match query")

        # 検証
        assert results == []

    @pytest.mark.asyncio
    async def test_search_by_text_bedrock_error(self) -> None:
        """Bedrock API呼び出しが失敗した場合に例外が伝播することを検証"""
        # モックの設定：BedrockClientが例外を投げる
        mock_bedrock_client = MagicMock()
        mock_s3_vector_client = MagicMock()

        mock_bedrock_client.generate_text_embedding = AsyncMock(
            side_effect=Exception("Bedrock API error")
        )

        base_url = "https://example.com"
        repository = LgtmImageSearchRepository(
            bedrock_client=mock_bedrock_client,
            s3_vector_client=mock_s3_vector_client,
            base_url=base_url,
        )

        # テスト実行と検証
        with pytest.raises(Exception) as exc_info:
            await repository.search_by_text("test query")

        assert "Bedrock API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_by_text_s3_vector_error(self) -> None:
        """S3 Vector API呼び出しが失敗した場合に例外が伝播することを検証"""
        # モックの設定：S3VectorClientが例外を投げる
        mock_bedrock_client = MagicMock()
        mock_s3_vector_client = MagicMock()

        mock_bedrock_client.generate_text_embedding = AsyncMock(
            return_value=[0.1, 0.2, 0.3]
        )
        mock_s3_vector_client.search_similar_vectors = AsyncMock(
            side_effect=Exception("S3 Vector API error")
        )

        base_url = "https://example.com"
        repository = LgtmImageSearchRepository(
            bedrock_client=mock_bedrock_client,
            s3_vector_client=mock_s3_vector_client,
            base_url=base_url,
        )

        # テスト実行と検証
        with pytest.raises(Exception) as exc_info:
            await repository.search_by_text("test query")

        assert "S3 Vector API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_by_text_raises_error_when_source_key_missing(self) -> None:
        """メタデータにsource_keyがない場合、ErrVectorDataCorruptedが発生することを検証"""
        # モックの設定
        mock_bedrock_client = MagicMock()
        mock_s3_vector_client = MagicMock()

        mock_bedrock_client.generate_text_embedding = AsyncMock(
            return_value=[0.1, 0.2, 0.3]
        )

        # メタデータにsource_keyがない検索結果
        mock_s3_vector_client.search_similar_vectors = AsyncMock(
            return_value=[
                {
                    "key": "123",
                    "distance": 0.1,
                    "metadata": {},  # source_keyなし
                },
            ]
        )

        base_url = "https://example.com"
        repository = LgtmImageSearchRepository(
            bedrock_client=mock_bedrock_client,
            s3_vector_client=mock_s3_vector_client,
            base_url=base_url,
        )

        # テスト実行と検証
        with pytest.raises(ErrVectorDataCorrupted) as exc_info:
            await repository.search_by_text("test query")

        assert "Vector data missing required 'source_key'" in str(exc_info.value)
        assert "123" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_by_text_raises_error_when_metadata_missing(self) -> None:
        """メタデータ自体がない場合、ErrVectorDataCorruptedが発生することを検証"""
        # モックの設定
        mock_bedrock_client = MagicMock()
        mock_s3_vector_client = MagicMock()

        mock_bedrock_client.generate_text_embedding = AsyncMock(
            return_value=[0.1, 0.2, 0.3]
        )

        # メタデータがない検索結果
        mock_s3_vector_client.search_similar_vectors = AsyncMock(
            return_value=[
                {
                    "key": "456",
                    "distance": 0.1,
                    # metadataキー自体がない
                },
            ]
        )

        base_url = "https://example.com"
        repository = LgtmImageSearchRepository(
            bedrock_client=mock_bedrock_client,
            s3_vector_client=mock_s3_vector_client,
            base_url=base_url,
        )

        # テスト実行と検証
        with pytest.raises(ErrVectorDataCorrupted) as exc_info:
            await repository.search_by_text("test query")

        assert "Vector data missing required 'source_key'" in str(exc_info.value)
        assert "456" in str(exc_info.value)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("distance_value", "expected_error_msg"),
        [
            (None, "Vector data missing 'distance' field for id: 123"),
            ("invalid", "Vector data has non-numeric distance for id: 123"),
            (-0.5, "Vector data has negative distance for id: 123"),
            (
                float("nan"),
                "Vector data has non-finite distance (NaN or inf) for id: 123",
            ),
            (
                float("inf"),
                "Vector data has non-finite distance (NaN or inf) for id: 123",
            ),
        ],
        ids=["missing", "non_numeric", "negative", "nan", "inf"],
    )
    async def test_search_by_text_raises_error_on_invalid_distance(
        self,
        distance_value: Any,
        expected_error_msg: str,
    ) -> None:
        """distanceフィールドが不正な値の場合、ErrVectorDataCorruptedを投げることを検証"""
        # モックの設定
        mock_bedrock_client = MagicMock()
        mock_s3_vector_client = MagicMock()

        mock_bedrock_client.generate_text_embedding = AsyncMock(
            return_value=[0.1, 0.2, 0.3, 0.4, 0.5]
        )

        # テストケースに応じた結果データを構築
        result_data: dict[str, Any] = {
            "key": "123",
            "metadata": {
                "source_key": "2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp"
            },
        }
        if distance_value is not None:
            result_data["distance"] = distance_value

        mock_s3_vector_client.search_similar_vectors = AsyncMock(
            return_value=[result_data]
        )

        base_url = "https://example.com"
        repository = LgtmImageSearchRepository(
            bedrock_client=mock_bedrock_client,
            s3_vector_client=mock_s3_vector_client,
            base_url=base_url,
        )

        # テスト実行: 例外が投げられることを検証
        with pytest.raises(ErrVectorDataCorrupted) as exc_info:
            await repository.search_by_text("test query", max_results=9)

        # エラーメッセージの確認
        assert expected_error_msg in str(exc_info.value)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "key_value",
        [None, ""],
        ids=["missing", "empty_string"],
    )
    async def test_search_by_text_raises_error_on_invalid_key(
        self,
        key_value: Any,
    ) -> None:
        """keyフィールドが不正な値の場合、ErrVectorDataCorruptedを投げることを検証"""
        # モックの設定
        mock_bedrock_client = MagicMock()
        mock_s3_vector_client = MagicMock()

        mock_bedrock_client.generate_text_embedding = AsyncMock(
            return_value=[0.1, 0.2, 0.3, 0.4, 0.5]
        )

        # テストケースに応じた結果データを構築
        result_data: dict[str, Any] = {
            "distance": 0.15,
            "metadata": {
                "source_key": "2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp"
            },
        }
        if key_value is not None:
            result_data["key"] = key_value

        mock_s3_vector_client.search_similar_vectors = AsyncMock(
            return_value=[result_data]
        )

        base_url = "https://example.com"
        repository = LgtmImageSearchRepository(
            bedrock_client=mock_bedrock_client,
            s3_vector_client=mock_s3_vector_client,
            base_url=base_url,
        )

        # テスト実行: 例外が投げられることを検証
        with pytest.raises(ErrVectorDataCorrupted) as exc_info:
            await repository.search_by_text("test query", max_results=9)

        # エラーメッセージの確認
        assert "Vector data missing required 'key' field" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_by_image_success(self) -> None:
        """正常に画像検索が実行できることを検証"""
        # モックの設定
        mock_bedrock_client = MagicMock()
        mock_s3_vector_client = MagicMock()

        # BedrockClientのモック：画像埋め込みベクトルを返す
        mock_bedrock_client.generate_image_embedding = AsyncMock(
            return_value=[0.1, 0.2, 0.3, 0.4, 0.5]
        )

        # S3VectorClientのモック：検索結果を返す（source_key含む）
        mock_s3_vector_client.search_similar_vectors = AsyncMock(
            return_value=[
                {
                    "key": "123",
                    "distance": 0.15,
                    "metadata": {
                        "source_key": "2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp"
                    },
                },
                {
                    "key": "456",
                    "distance": 0.25,
                    "metadata": {
                        "source_key": "2021/03/17/12/6947f291-a46e-453c-a230-0d756d7174cc.webp"
                    },
                },
            ]
        )

        base_url = "example.com"
        repository = LgtmImageSearchRepository(
            bedrock_client=mock_bedrock_client,
            s3_vector_client=mock_s3_vector_client,
            base_url=base_url,
        )

        # テスト実行
        test_image_data = "base64encodedimagedata"
        results = await repository.search_by_image(
            test_image_data, ".png", max_results=9
        )

        # 検証
        assert len(results) == 2

        # 1件目の検証
        assert results[0]["id"] == "123"
        assert (
            results[0]["url"]
            == "https://example.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp"
        )
        # distance=0.15 -> similarity_score=1.0/(1.0+0.15)≒0.8696
        assert results[0]["similarity_score"] == pytest.approx(1.0 / 1.15)

        # 2件目の検証
        assert results[1]["id"] == "456"
        assert (
            results[1]["url"]
            == "https://example.com/2021/03/17/12/6947f291-a46e-453c-a230-0d756d7174cc.webp"
        )
        # distance=0.25 -> similarity_score=1.0/(1.0+0.25)=0.8
        assert results[1]["similarity_score"] == pytest.approx(0.8)

        # モックメソッドの呼び出しを検証
        mock_bedrock_client.generate_image_embedding.assert_called_once_with(
            test_image_data, ".png"
        )
        mock_s3_vector_client.search_similar_vectors.assert_called_once_with(
            [0.1, 0.2, 0.3, 0.4, 0.5], 9
        )

    @pytest.mark.asyncio
    async def test_search_by_image_empty_result(self) -> None:
        """画像検索で結果が0件の場合を検証"""
        # モックの設定
        mock_bedrock_client = MagicMock()
        mock_s3_vector_client = MagicMock()

        # BedrockClientのモック：画像埋め込みベクトルを返す
        mock_bedrock_client.generate_image_embedding = AsyncMock(
            return_value=[0.1, 0.2, 0.3, 0.4, 0.5]
        )

        # S3VectorClientのモック：空の結果を返す
        mock_s3_vector_client.search_similar_vectors = AsyncMock(return_value=[])

        base_url = "example.com"
        repository = LgtmImageSearchRepository(
            bedrock_client=mock_bedrock_client,
            s3_vector_client=mock_s3_vector_client,
            base_url=base_url,
        )

        # テスト実行
        results = await repository.search_by_image(
            "base64encodedimagedata", ".png", max_results=9
        )

        # 検証
        assert len(results) == 0
        assert results == []

    @pytest.mark.asyncio
    async def test_search_by_image_bedrock_error(self) -> None:
        """BedrockClientでエラーが発生した場合を検証"""
        # モックの設定
        mock_bedrock_client = MagicMock()
        mock_s3_vector_client = MagicMock()

        # BedrockClientのモック：エラーを発生させる
        mock_bedrock_client.generate_image_embedding = AsyncMock(
            side_effect=ErrEmbeddingGenerationFailed("Bedrock API error")
        )

        base_url = "example.com"
        repository = LgtmImageSearchRepository(
            bedrock_client=mock_bedrock_client,
            s3_vector_client=mock_s3_vector_client,
            base_url=base_url,
        )

        # テスト実行と検証
        with pytest.raises(ErrEmbeddingGenerationFailed):
            await repository.search_by_image(
                "base64encodedimagedata", ".png", max_results=9
            )

    @pytest.mark.asyncio
    async def test_search_by_image_s3_vector_error(self) -> None:
        """S3 Vector検索でエラーが発生した場合を検証"""
        # モックの設定
        mock_bedrock_client = MagicMock()
        mock_s3_vector_client = MagicMock()

        # BedrockClientのモック：画像埋め込みベクトルを返す
        mock_bedrock_client.generate_image_embedding = AsyncMock(
            return_value=[0.1, 0.2, 0.3, 0.4, 0.5]
        )

        # S3VectorClientのモック：エラーを発生させる
        mock_s3_vector_client.search_similar_vectors = AsyncMock(
            side_effect=Exception("S3 Vector API error")
        )

        base_url = "example.com"
        repository = LgtmImageSearchRepository(
            bedrock_client=mock_bedrock_client,
            s3_vector_client=mock_s3_vector_client,
            base_url=base_url,
        )

        # テスト実行と検証
        with pytest.raises(Exception) as exc_info:
            await repository.search_by_image(
                "base64encodedimagedata", ".png", max_results=9
            )
        assert "S3 Vector API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_by_image_raises_error_when_source_key_missing(self) -> None:
        """metadataにsource_keyが含まれていない場合のエラー処理を検証"""
        # モックの設定
        mock_bedrock_client = MagicMock()
        mock_s3_vector_client = MagicMock()

        # BedrockClientのモック：画像埋め込みベクトルを返す
        mock_bedrock_client.generate_image_embedding = AsyncMock(
            return_value=[0.1, 0.2, 0.3, 0.4, 0.5]
        )

        # S3VectorClientのモック：source_keyが欠落している結果を返す
        mock_s3_vector_client.search_similar_vectors = AsyncMock(
            return_value=[
                {
                    "key": "123",
                    "distance": 0.15,
                    "metadata": {},  # source_keyがない
                }
            ]
        )

        base_url = "example.com"
        repository = LgtmImageSearchRepository(
            bedrock_client=mock_bedrock_client,
            s3_vector_client=mock_s3_vector_client,
            base_url=base_url,
        )

        # テスト実行と検証
        with pytest.raises(ErrVectorDataCorrupted) as exc_info:
            await repository.search_by_image(
                "base64encodedimagedata", ".png", max_results=9
            )
        assert "missing required 'source_key' in metadata" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_by_image_raises_error_when_metadata_missing(self) -> None:
        """メタデータ自体がない場合、ErrVectorDataCorruptedが発生することを検証"""
        # モックの設定
        mock_bedrock_client = MagicMock()
        mock_s3_vector_client = MagicMock()

        # BedrockClientのモック：画像埋め込みベクトルを返す
        mock_bedrock_client.generate_image_embedding = AsyncMock(
            return_value=[0.1, 0.2, 0.3, 0.4, 0.5]
        )

        # S3VectorClientのモック：メタデータがない結果を返す
        mock_s3_vector_client.search_similar_vectors = AsyncMock(
            return_value=[
                {
                    "key": "456",
                    "distance": 0.1,
                    # metadataキー自体がない
                }
            ]
        )

        base_url = "example.com"
        repository = LgtmImageSearchRepository(
            bedrock_client=mock_bedrock_client,
            s3_vector_client=mock_s3_vector_client,
            base_url=base_url,
        )

        # テスト実行と検証
        with pytest.raises(ErrVectorDataCorrupted) as exc_info:
            await repository.search_by_image(
                "base64encodedimagedata", ".png", max_results=9
            )

        assert "Vector data missing required 'source_key'" in str(exc_info.value)
        assert "456" in str(exc_info.value)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("distance_value", "expected_error_msg"),
        [
            (None, "Vector data missing 'distance' field for id: 123"),
            ("invalid", "Vector data has non-numeric distance for id: 123"),
            (-0.5, "Vector data has negative distance for id: 123"),
            (
                float("nan"),
                "Vector data has non-finite distance (NaN or inf) for id: 123",
            ),
            (
                float("inf"),
                "Vector data has non-finite distance (NaN or inf) for id: 123",
            ),
        ],
        ids=["missing", "non_numeric", "negative", "nan", "inf"],
    )
    async def test_search_by_image_raises_error_on_invalid_distance(
        self,
        distance_value: Any,
        expected_error_msg: str,
    ) -> None:
        """distanceフィールドが不正な値の場合、ErrVectorDataCorruptedを投げることを検証"""
        # モックの設定
        mock_bedrock_client = MagicMock()
        mock_s3_vector_client = MagicMock()

        mock_bedrock_client.generate_image_embedding = AsyncMock(
            return_value=[0.1, 0.2, 0.3, 0.4, 0.5]
        )

        # テストケースに応じた結果データを構築
        result_data: dict[str, Any] = {
            "key": "123",
            "metadata": {
                "source_key": "2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp"
            },
        }
        if distance_value is not None:
            result_data["distance"] = distance_value

        mock_s3_vector_client.search_similar_vectors = AsyncMock(
            return_value=[result_data]
        )

        base_url = "https://example.com"
        repository = LgtmImageSearchRepository(
            bedrock_client=mock_bedrock_client,
            s3_vector_client=mock_s3_vector_client,
            base_url=base_url,
        )

        # テスト実行: 例外が投げられることを検証
        with pytest.raises(ErrVectorDataCorrupted) as exc_info:
            await repository.search_by_image(
                "base64encodedimagedata", ".png", max_results=9
            )

        # エラーメッセージの確認
        assert expected_error_msg in str(exc_info.value)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "key_value",
        [None, ""],
        ids=["missing", "empty_string"],
    )
    async def test_search_by_image_raises_error_on_invalid_key(
        self,
        key_value: Any,
    ) -> None:
        """keyフィールドが不正な値の場合、ErrVectorDataCorruptedを投げることを検証"""
        # モックの設定
        mock_bedrock_client = MagicMock()
        mock_s3_vector_client = MagicMock()

        mock_bedrock_client.generate_image_embedding = AsyncMock(
            return_value=[0.1, 0.2, 0.3, 0.4, 0.5]
        )

        # テストケースに応じた結果データを構築
        result_data: dict[str, Any] = {
            "distance": 0.15,
            "metadata": {
                "source_key": "2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp"
            },
        }
        if key_value is not None:
            result_data["key"] = key_value

        mock_s3_vector_client.search_similar_vectors = AsyncMock(
            return_value=[result_data]
        )

        base_url = "https://example.com"
        repository = LgtmImageSearchRepository(
            bedrock_client=mock_bedrock_client,
            s3_vector_client=mock_s3_vector_client,
            base_url=base_url,
        )

        # テスト実行: 例外が投げられることを検証
        with pytest.raises(ErrVectorDataCorrupted) as exc_info:
            await repository.search_by_image(
                "base64encodedimagedata", ".png", max_results=9
            )

        # エラーメッセージの確認
        assert "Vector data missing required 'key' field" in str(exc_info.value)
