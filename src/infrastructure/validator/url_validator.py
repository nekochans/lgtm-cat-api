# 絶対厳守:編集前に必ずAI実装ルールを読む

from urllib.parse import urlparse

from domain.lgtm_image_errors import ErrInvalidUrl


def validate_allowed_domain(url: str, allowed_domain: str) -> None:
    if not url or not isinstance(url, str):
        raise ErrInvalidUrl("URL must be a non-empty string")

    if not isinstance(allowed_domain, str) or not allowed_domain.strip():
        raise ErrInvalidUrl("Allowed domain is not configured")

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ErrInvalidUrl(f"Failed to parse URL: {e}") from e

    # スキームのチェック(httpsのみ許可)
    if parsed.scheme != "https":
        raise ErrInvalidUrl(
            f"Invalid URL scheme: {parsed.scheme}. Only https is allowed"
        )

    # ホスト名が存在するかチェック
    if not parsed.hostname:
        raise ErrInvalidUrl("URL must contain a valid hostname")

    # 許可されたR2ドメインかチェック(大文字小文字を区別しない)
    if parsed.hostname.lower() != allowed_domain.lower():
        raise ErrInvalidUrl(
            f"URL domain '{parsed.hostname}' is not allowed. Only '{allowed_domain}' is permitted"
        )
