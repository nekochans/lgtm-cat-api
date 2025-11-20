# 絶対厳守：編集前に必ずAI実装ルールを読む

import math
from typing import Any

from domain.lgtm_image_errors import ErrVectorDataCorrupted
from domain.lgtm_image_search import (
    DEFAULT_SEARCH_MAX_RESULTS,
    LgtmImageSearchResult,
)
from domain.repository.lgtm_image_search_repository_interface import (
    LgtmImageSearchRepositoryInterface,
)
from infrastructure.bedrock_client import BedrockClient
from infrastructure.s3_vector_client import S3VectorClient


class LgtmImageSearchRepository(LgtmImageSearchRepositoryInterface):
    """LGTM画像検索リポジトリの実装"""

    def __init__(
        self,
        bedrock_client: BedrockClient,
        s3_vector_client: S3VectorClient,
        base_url: str,
    ) -> None:
        self.bedrock_client = bedrock_client
        self.s3_vector_client = s3_vector_client
        self.base_url = base_url

    def _convert_search_results(
        self, search_results: list[dict[str, Any]]
    ) -> list[LgtmImageSearchResult]:
        results: list[LgtmImageSearchResult] = []
        for result in search_results:
            # keyにはDB IDが格納されている - まず存在をチェック
            image_id = result.get("key")
            if not image_id:
                raise ErrVectorDataCorrupted(
                    "Vector data missing required 'key' field (image ID)"
                )

            # metadataからS3キーを取得してURLを構築
            metadata = result.get("metadata", {})
            source_key = metadata.get("source_key")

            if not source_key:
                raise ErrVectorDataCorrupted(
                    f"Vector data missing required 'source_key' in metadata for id: {image_id}"
                )

            # 例: "2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp"
            image_url = f"https://{self.base_url}/{source_key}"

            # distanceフィールドを厳密に検証
            # S3 Vectorはdistance(距離)を返す(小さいほど類似度が高い)
            if "distance" not in result:
                raise ErrVectorDataCorrupted(
                    f"Vector data missing 'distance' field for id: {image_id}"
                )

            distance_value = result["distance"]

            # distanceが数値(int/float)で、非負かつ有限(NaN/infではない)であることを検証
            if not isinstance(distance_value, (int, float)):
                raise ErrVectorDataCorrupted(
                    f"Vector data has non-numeric distance for id: {image_id}, "
                    f"got type {type(distance_value).__name__}"
                )

            if distance_value < 0:
                raise ErrVectorDataCorrupted(
                    f"Vector data has negative distance for id: {image_id}, "
                    f"distance={distance_value}"
                )

            # NaN/infチェック
            if not math.isfinite(distance_value):
                raise ErrVectorDataCorrupted(
                    f"Vector data has non-finite distance (NaN or inf) for id: {image_id}, "
                    f"distance={distance_value}"
                )

            # 0-1の範囲のスコアに変換し、高いほど類似度が高くなるようにする
            similarity_score = 1.0 / (1.0 + distance_value)

            results.append(
                LgtmImageSearchResult(
                    id=image_id,
                    url=image_url,
                    similarity_score=similarity_score,
                )
            )

        return results

    async def search_by_text(
        self, query_text: str, max_results: int = DEFAULT_SEARCH_MAX_RESULTS
    ) -> list[LgtmImageSearchResult]:
        query_vector = await self.bedrock_client.generate_text_embedding(query_text)

        search_results = await self.s3_vector_client.search_similar_vectors(
            query_vector, max_results
        )

        return self._convert_search_results(search_results)

    async def search_by_image(
        self,
        image_data: str,
        image_extension: str,
        max_results: int = DEFAULT_SEARCH_MAX_RESULTS,
    ) -> list[LgtmImageSearchResult]:
        query_vector = await self.bedrock_client.generate_image_embedding(
            image_data, image_extension
        )

        search_results = await self.s3_vector_client.search_similar_vectors(
            query_vector, max_results
        )

        return self._convert_search_results(search_results)
