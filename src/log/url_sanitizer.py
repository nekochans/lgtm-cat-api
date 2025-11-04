# 絶対厳守：編集前に必ずAI実装ルールを読む
"""ログ用URL サニタイゼーション機能."""

from urllib.parse import urlsplit, urlunsplit


def sanitize_url_for_logging(url: str) -> str:
    """
    URLから機密情報(認証情報、クエリパラメータ、フラグメント)を除去してログ用に安全な形式にする.

    Args:
        url: サニタイズ対象のURL

    Returns:
        スキーム、ホスト名、パスのみを含む安全なURL文字列
        入力が不正な場合は空文字列を返す
    """
    # 入力検証: Noneまたは空文字列の場合は空文字列を返す
    if not url:
        return ""

    try:
        parsed = urlsplit(url)

        # 認証情報を除去したnetlocを再構築
        # hostname と port のみを使用し、username と password を除外
        hostname = parsed.hostname or ""
        # IPv6 addresses must be wrapped in brackets
        if ":" in hostname:  # IPv6 address detected
            if parsed.port:
                clean_netloc = f"[{hostname}]:{parsed.port}"
            else:
                clean_netloc = f"[{hostname}]"
        elif parsed.port:
            clean_netloc = f"{hostname}:{parsed.port}"
        else:
            clean_netloc = hostname

        # クエリ文字列とフラグメントを空にし、認証情報を除去して再構築
        sanitized = urlunsplit((parsed.scheme, clean_netloc, parsed.path, "", ""))
        return sanitized

    except (ValueError, AttributeError):
        # 不正なURL形式の場合は空文字列を返す
        return ""
