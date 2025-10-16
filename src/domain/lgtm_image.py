# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Final, NewType, Required, TypedDict


# LGTM画像のID型（intと区別して型安全性を向上）
LgtmImageId = NewType("LgtmImageId", int)

DEFAULT_RANDOM_IMAGES_LIMIT: Final[int] = 9


class LgtmImage(TypedDict):
    id: Required[str]
    url: Required[str]
