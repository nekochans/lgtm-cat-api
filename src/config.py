# 絶対厳守:編集前に必ずAI実装ルールを読む

import os
from typing import Final, Optional

# 環境変数から画像のベースURLを取得（デフォルト値を設定）
LGTM_IMAGES_BASE_URL: Final[str] = os.getenv(
    "LGTM_IMAGES_BASE_URL", "lgtm-images.lgtmeow.com"
)

# S3アップロード用バケット名
UPLOAD_S3_BUCKET_NAME: Final[str] = os.getenv("UPLOAD_S3_BUCKET_NAME", "")

# ログレベル設定（デフォルト: INFO）
LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO")

# AWS Cognito設定
COGNITO_REGION: Final[str] = os.getenv("COGNITO_REGION", "ap-northeast-1")

# Sentry設定
SENTRY_DSN: Final[str] = os.getenv("SENTRY_DSN", "")
SENTRY_ENVIRONMENT: Final[str] = os.getenv("SENTRY_ENVIRONMENT", "development")

# 必須の環境変数（Noneを許可するが、起動時に検証が必要）
_cognito_user_pool_id: Optional[str] = os.getenv("COGNITO_USER_POOL_ID")
_cognito_app_client_id: Optional[str] = os.getenv("COGNITO_APP_CLIENT_ID")

# NOTE: これらの定数は validate_required_config() が成功した後のみ安全にアクセス可能
COGNITO_USER_POOL_ID: Final[str] = _cognito_user_pool_id or ""
COGNITO_APP_CLIENT_ID: Final[str] = _cognito_app_client_id or ""


def validate_required_config() -> None:
    missing_vars = []

    if not _cognito_user_pool_id:
        missing_vars.append("COGNITO_USER_POOL_ID")

    if not _cognito_app_client_id:
        missing_vars.append("COGNITO_APP_CLIENT_ID")

    if missing_vars:
        error_msg = (
            f"Required environment variable(s) not set: {', '.join(missing_vars)}"
        )
        raise RuntimeError(error_msg)


def get_lgtm_images_base_url() -> str:
    return LGTM_IMAGES_BASE_URL


def get_upload_s3_bucket_name() -> str:
    return UPLOAD_S3_BUCKET_NAME


def get_log_level() -> str:
    return LOG_LEVEL


def get_cognito_region() -> str:
    return COGNITO_REGION


def get_cognito_user_pool_id() -> str:
    return COGNITO_USER_POOL_ID


def get_cognito_app_client_id() -> str:
    return COGNITO_APP_CLIENT_ID


def get_sentry_dsn() -> str:
    return SENTRY_DSN


def get_sentry_environment() -> str:
    return SENTRY_ENVIRONMENT
