# 絶対厳守：編集前に必ずAI実装ルールを読む

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domain.lgtm_image_errors import ErrEmbeddingGenerationFailed
from infrastructure.bedrock_client import BedrockClient


class TestBedrockClient:
    @pytest.fixture
    def mock_bedrock_response(self) -> dict[str, Any]:
        """モックBedrockレスポンスを返すフィクスチャ（embedding_types指定時の形式）"""
        return {"embeddings": {"float": [[0.1, 0.2, 0.3, 0.4, 0.5]]}}

    @pytest.mark.asyncio
    @patch("infrastructure.bedrock_client.aioboto3.Session")
    async def test_generate_text_embedding_success(
        self,
        mock_session_class: MagicMock,
        mock_bedrock_response: dict[str, Any],
    ) -> None:
        """正常にテキストの埋め込みが生成できることを検証"""
        # モックレスポンスの設定
        response_body = json.dumps(mock_bedrock_response)
        mock_body = AsyncMock()
        mock_body.read = AsyncMock(return_value=response_body.encode("utf-8"))
        mock_response = {
            "body": mock_body,
        }

        # aioboto3のセッションとクライアントをモック
        mock_client = AsyncMock()
        mock_client.invoke_model = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.client = MagicMock(return_value=mock_client)
        mock_session_class.return_value = mock_session

        bedrock_client = BedrockClient(region="us-east-1", model_id="cohere.embed-v4:0")

        # テスト実行
        result = await bedrock_client.generate_text_embedding("test query")

        # 検証
        assert result == [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_client.invoke_model.assert_called_once()

        # invoke_modelの引数を検証
        call_args = mock_client.invoke_model.call_args
        assert call_args[1]["modelId"] == "cohere.embed-v4:0"
        assert call_args[1]["contentType"] == "application/json"
        assert call_args[1]["accept"] == "application/json"

        # リクエストボディの検証
        request_body = json.loads(call_args[1]["body"])
        assert request_body["texts"] == ["test query"]
        assert request_body["input_type"] == "search_query"
        assert request_body["embedding_types"] == ["float"]

    @pytest.mark.asyncio
    @patch("infrastructure.bedrock_client.aioboto3.Session")
    async def test_generate_text_embedding_api_error(
        self,
        mock_session_class: MagicMock,
    ) -> None:
        """Bedrock API呼び出しが失敗した場合にErrEmbeddingGenerationFailedが発生することを検証"""
        # モックの設定：invoke_modelが例外を投げる
        mock_client = AsyncMock()
        mock_client.invoke_model = AsyncMock(
            side_effect=Exception("Bedrock API call failed")
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.client = MagicMock(return_value=mock_client)
        mock_session_class.return_value = mock_session

        bedrock_client = BedrockClient(region="us-east-1", model_id="cohere.embed-v4:0")

        # テスト実行と検証
        with pytest.raises(ErrEmbeddingGenerationFailed) as exc_info:
            await bedrock_client.generate_text_embedding("test query")

        # エラーメッセージにモデルIDとエラー型が含まれることを確認
        assert "Failed to invoke Bedrock model" in str(exc_info.value)
        assert "Exception" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("infrastructure.bedrock_client.aioboto3.Session")
    async def test_generate_text_embedding_no_float_embeddings(
        self,
        mock_session_class: MagicMock,
    ) -> None:
        """レスポンスにfloat埋め込みがない場合にエラーが発生することを検証"""
        # モックレスポンスの設定：floatキーがない
        mock_response_data = {"embeddings": {"int8": [[1, 2, 3]]}}  # floatがない
        response_body = json.dumps(mock_response_data)
        mock_body = AsyncMock()
        mock_body.read = AsyncMock(return_value=response_body.encode("utf-8"))
        mock_response = {
            "body": mock_body,
        }

        mock_client = AsyncMock()
        mock_client.invoke_model = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.client = MagicMock(return_value=mock_client)
        mock_session_class.return_value = mock_session

        bedrock_client = BedrockClient(region="us-east-1", model_id="cohere.embed-v4:0")

        # テスト実行と検証
        with pytest.raises(ErrEmbeddingGenerationFailed) as exc_info:
            await bedrock_client.generate_text_embedding("test query")

        assert "No float embeddings found in response" in str(exc_info.value)
