# 絶対厳守:編集前に必ずAI実装ルールを読む

import os
from typing import Final

# 環境変数から画像のベースURLを取得（デフォルト値を設定）
LGTM_IMAGES_BASE_URL: Final[str] = os.getenv(
    "LGTM_IMAGES_BASE_URL", "lgtm-images.lgtmeow.com"
)


def get_lgtm_images_base_url() -> str:
    return LGTM_IMAGES_BASE_URL
