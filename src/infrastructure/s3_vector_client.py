# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Any

import aioboto3


from botocore.exceptions import BotoCoreError, ClientError

from domain.lgtm_image_errors import ErrVectorSearchFailed

from log.logger import get_logger

logger = get_logger(__name__)


class S3VectorClient:
    def __init__(self, region: str, bucket_name: str, index_name: str) -> None:
        self.region = region
        self.bucket_name = bucket_name
        self.index_name = index_name
        self.session = aioboto3.Session()

    async def search_similar_vectors(
        self, query_vector: list[float], max_results: int
    ) -> list[dict[str, Any]]:
        try:
            async with self.session.client(
                "s3vectors", region_name=self.region
            ) as client:
                response = await client.query_vectors(
                    vectorBucketName=self.bucket_name,
                    indexName=self.index_name,
                    queryVector={"float32": query_vector},
                    topK=max_results,
                    returnDistance=True,
                    returnMetadata=True,
                )
        except (ClientError, BotoCoreError) as e:
            # ClientErrorの場合はerror_codeを取得、BotoCoreErrorの場合はNone
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code")
            logger.error(
                f"AWS API call failed: {type(e).__name__}",
                extra={
                    "bucket_name": self.bucket_name,
                    "index_name": self.index_name,
                    "error_type": type(e).__name__,
                    "error_code": error_code,
                    "error_message": str(e),
                },
            )
            raise ErrVectorSearchFailed(
                f"Failed to query S3 Vector index '{self.index_name}' "
                f"in bucket '{self.bucket_name}': {type(e).__name__}"
            ) from e
        except Exception as e:
            logger.error(
                "Failed to query S3 Vector index: Unexpected error",
                extra={
                    "bucket_name": self.bucket_name,
                    "index_name": self.index_name,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
            )
            raise ErrVectorSearchFailed(
                f"Failed to query S3 Vector index '{self.index_name}' "
                f"in bucket '{self.bucket_name}': {type(e).__name__}"
            ) from e

        # レスポンスから結果を抽出
        vectors = response.get("vectors", [])
        results: list[dict[str, Any]] = []

        for vector in vectors:
            # デフォルト値を使わず、そのまま返す
            # 呼び出し元(lgtm_image_search_repository)でバリデーション済み
            results.append(
                {
                    "key": vector.get("key"),
                    "distance": vector.get("distance"),
                    "metadata": vector.get("metadata"),
                }
            )

        return results
