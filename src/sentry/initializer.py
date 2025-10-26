# 絶対厳守:編集前に必ずAI実装ルールを読む

import logging
from typing import Any, Optional

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration


logger = logging.getLogger(__name__)


def init_sentry(
    dsn: str,
    environment: str,
) -> None:
    if not dsn:
        logger.info("Sentry DSN is not set. Skipping Sentry initialization.")
        return

    # 環境に応じてサンプリングレートを設定
    traces_sample_rate = 0.2 if environment == "production" else 0.05
    profiles_sample_rate = 0.1 if environment == "production" else 0.01

    # ロギング統合の設定
    # WARNING以上のログをSentryのbreadcrumbsとして記録
    # ERRORレベル以上のログはSentryのイベントとして送信
    logging_integration = LoggingIntegration(
        level=logging.WARNING, event_level=logging.ERROR
    )

    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            integrations=[logging_integration],
            send_default_pii=False,
        )

        logger.info(
            f"Sentry initialized. Environment: {environment}, "
            f"Traces sample rate: {traces_sample_rate}, "
            f"Profiles sample rate: {profiles_sample_rate}"
        )
    except Exception:
        logger.error("Failed to initialize Sentry", exc_info=True)
        raise


def capture_exception(error: Exception, extra: Optional[dict[str, Any]] = None) -> None:
    if extra:
        with sentry_sdk.push_scope() as scope:
            for key, value in extra.items():
                scope.set_extra(key, value)
            sentry_sdk.capture_exception(error)
    else:
        sentry_sdk.capture_exception(error)
