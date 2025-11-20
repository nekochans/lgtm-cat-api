# 絶対厳守：編集前に必ずAI実装ルールを読む

import json

import aioboto3

from domain.image_format import extension_to_mime_type
from domain.lgtm_image_errors import ErrEmbeddingGenerationFailed

from botocore.exceptions import BotoCoreError, ClientError

from log.logger import get_logger

logger = get_logger(__name__)


class BedrockClient:
    def __init__(self, region: str, model_id: str) -> None:
        self.region = region
        self.model_id = model_id
        self.session = aioboto3.Session()

    async def _invoke_bedrock_model(self, body: str) -> list[float]:
        try:
            async with self.session.client(
                "bedrock-runtime", region_name=self.region
            ) as client:
                response = await client.invoke_model(
                    modelId=self.model_id,
                    body=body,
                    contentType="application/json",
                    accept="application/json",
                )
                # async withブロックの中でresponse bodyを読み取る
                response_body = json.loads(await response["body"].read())
        except (ClientError, BotoCoreError) as e:
            # ClientErrorの場合はerror_codeを取得、BotoCoreErrorの場合はNone
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code")
            logger.error(
                f"AWS API call failed: {type(e).__name__}",
                extra={
                    "model_id": self.model_id,
                    "error_type": type(e).__name__,
                    "error_code": error_code,
                    "error_message": str(e),
                },
            )
            raise ErrEmbeddingGenerationFailed(
                f"Failed to invoke Bedrock model: {type(e).__name__}"
            ) from e
        except Exception as e:
            logger.error(
                "Failed to invoke Bedrock model: Unexpected error",
                extra={
                    "model_id": self.model_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
            )
            raise ErrEmbeddingGenerationFailed(
                f"Failed to invoke Bedrock model: {type(e).__name__}"
            ) from e

        # embedding_typesを指定した場合のレスポンス形式:
        # {"embeddings": {"float": [[float, float, ...]]}}
        embeddings_by_type = response_body.get("embeddings", {})
        float_embeddings = embeddings_by_type.get("float", [])
        if not float_embeddings:
            raise ErrEmbeddingGenerationFailed("No float embeddings found in response")
        embeddings: list[float] = float_embeddings[0]
        return embeddings

    async def generate_text_embedding(self, text: str) -> list[float]:
        body = json.dumps(
            {
                "texts": [text],
                "input_type": "search_query",
                "embedding_types": ["float"],
            }
        )
        return await self._invoke_bedrock_model(body)

    async def generate_image_embedding(
        self, image_data: str, image_extension: str
    ) -> list[float]:
        mime_type = extension_to_mime_type(image_extension)

        data_uri = f"data:{mime_type};base64,{image_data}"

        body = json.dumps(
            {
                "images": [data_uri],
                "input_type": "search_query",
                "embedding_types": ["float"],
            }
        )

        return await self._invoke_bedrock_model(body)
