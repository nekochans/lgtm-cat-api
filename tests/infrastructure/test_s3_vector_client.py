# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from infrastructure.s3_vector_client import S3VectorClient


from domain.lgtm_image_errors import ErrVectorSearchFailed


class TestS3VectorClient:
    @pytest.fixture
    def mock_s3vectors_response(self) -> dict[str, Any]:
        """モックS3 Vectorsレスポンスを返すフィクスチャ"""
        return {
            "vectors": [
                {
                    "key": "1",
                    "distance": 0.12345,
                    "metadata": {
                        "source_key": "2024/01/15/10/a1b2c3d4-e5f6-7890-abcd-ef1234567890.webp"
                    },
                },
                {
                    "key": "2",
                    "distance": 0.28734,
                    "metadata": {
                        "source_key": "2024/02/20/14/b2c3d4e5-f6a7-8901-bcde-f12345678901.webp"
                    },
                },
            ],
            "distanceMetric": "cosine",
        }

    @pytest.mark.asyncio
    @patch("infrastructure.s3_vector_client.aioboto3.Session")
    async def test_search_similar_vectors_success(
        self,
        mock_session_class: MagicMock,
        mock_s3vectors_response: dict[str, Any],
    ) -> None:
        """正常に類似ベクトルを検索できることを検証"""
        # aioboto3のセッションとクライアントをモック
        mock_client = AsyncMock()
        mock_client.query_vectors = AsyncMock(return_value=mock_s3vectors_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.client = MagicMock(return_value=mock_client)
        mock_session_class.return_value = mock_session

        s3_vector_client = S3VectorClient(
            region="us-west-2", bucket_name="test-bucket", index_name="test-index"
        )

        # テスト実行
        query_vector = [0.1, 0.2, 0.3]
        result = await s3_vector_client.search_similar_vectors(
            query_vector, max_results=9
        )

        # 検証
        assert len(result) == 2
        assert result[0]["key"] == "1"
        assert result[0]["distance"] == 0.12345
        assert (
            result[0]["metadata"]["source_key"]
            == "2024/01/15/10/a1b2c3d4-e5f6-7890-abcd-ef1234567890.webp"
        )
        assert result[1]["key"] == "2"
        assert result[1]["distance"] == 0.28734
        assert (
            result[1]["metadata"]["source_key"]
            == "2024/02/20/14/b2c3d4e5-f6a7-8901-bcde-f12345678901.webp"
        )

        # query_vectorsの呼び出しを検証
        mock_client.query_vectors.assert_called_once()
        call_args = mock_client.query_vectors.call_args[1]
        assert call_args["vectorBucketName"] == "test-bucket"
        assert call_args["indexName"] == "test-index"
        assert call_args["queryVector"] == {"float32": query_vector}
        assert call_args["topK"] == 9
        assert call_args["returnDistance"] is True
        assert call_args["returnMetadata"] is True

    @pytest.mark.asyncio
    @patch("infrastructure.s3_vector_client.aioboto3.Session")
    async def test_search_similar_vectors_empty_result(
        self,
        mock_session_class: MagicMock,
    ) -> None:
        """検索結果が空の場合を検証"""
        # aioboto3のセッションとクライアントをモック
        mock_client = AsyncMock()
        mock_client.query_vectors = AsyncMock(return_value={"vectors": []})
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.client = MagicMock(return_value=mock_client)
        mock_session_class.return_value = mock_session

        s3_vector_client = S3VectorClient(
            region="us-west-2", bucket_name="test-bucket", index_name="test-index"
        )

        # テスト実行
        query_vector = [0.1, 0.2, 0.3]
        result = await s3_vector_client.search_similar_vectors(
            query_vector, max_results=9
        )

        # 検証
        assert result == []

    @pytest.mark.asyncio
    @patch("infrastructure.s3_vector_client.aioboto3.Session")
    async def test_search_similar_vectors_api_error(
        self,
        mock_session_class: MagicMock,
    ) -> None:
        """S3 Vectors API呼び出しが失敗した場合にErrVectorSearchFailedが発生することを検証"""
        # aioboto3のセッションとクライアントをモック
        mock_client = AsyncMock()
        mock_client.query_vectors = AsyncMock(
            side_effect=Exception("S3 Vectors API call failed")
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.client = MagicMock(return_value=mock_client)
        mock_session_class.return_value = mock_session

        s3_vector_client = S3VectorClient(
            region="us-west-2", bucket_name="test-bucket", index_name="test-index"
        )

        # テスト実行と検証
        query_vector = [0.1, 0.2, 0.3]
        with pytest.raises(ErrVectorSearchFailed) as exc_info:
            await s3_vector_client.search_similar_vectors(query_vector, max_results=9)

        # エラーメッセージの検証
        assert "Failed to query S3 Vector index 'test-index'" in str(exc_info.value)
        assert "in bucket 'test-bucket'" in str(exc_info.value)
        assert "Exception" in str(exc_info.value)
