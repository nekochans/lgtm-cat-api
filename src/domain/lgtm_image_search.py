# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Final, Required, TypedDict


class LgtmImageSearchResult(TypedDict):
    id: Required[str]
    url: Required[str]
    similarity_score: Required[float]  # 類似度スコア（0.0〜1.0）


# 検索結果のデフォルト最大件数
DEFAULT_SEARCH_MAX_RESULTS: Final[int] = 9
