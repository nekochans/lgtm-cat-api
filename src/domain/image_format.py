# 絶対厳守:編集前に必ずAI実装ルールを読む

from domain.lgtm_image_errors import ErrInvalidImageExtension

# MIMEタイプから拡張子へのマッピング(単一の情報源)
_MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
}

# 許可される画像のMIMEタイプ(後方互換性のため_MIME_TO_EXTから派生)
ALLOWED_IMAGE_MIME_TYPES = list(_MIME_TO_EXT.keys())


def mime_type_to_extension(mime_type: str) -> str:
    mime_to_ext = _MIME_TO_EXT

    # MIME typeを正規化(トリム + 小文字化)して大文字小文字を区別しない検索を行う
    normalized_mime_type = mime_type.strip().lower()

    extension = mime_to_ext.get(normalized_mime_type)
    if extension is None:
        raise ErrInvalidImageExtension(
            f"Unsupported MIME type: {normalized_mime_type}. Expected image/jpeg or image/png"
        )

    return extension
