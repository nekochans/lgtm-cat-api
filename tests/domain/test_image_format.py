# 絶対厳守:編集前に必ずAI実装ルールを読む

import pytest

from domain.image_format import mime_type_to_extension
from domain.lgtm_image_errors import ErrInvalidImageExtension


class TestMimeTypeToExtension:
    def test_convert_png_mime_type(self) -> None:
        """image/pngを.pngに変換する."""
        # Act
        result = mime_type_to_extension("image/png")

        # Assert
        assert result == ".png"

    def test_convert_jpeg_mime_type(self) -> None:
        """image/jpegを.jpgに変換する."""
        # Act
        result = mime_type_to_extension("image/jpeg")

        # Assert
        assert result == ".jpg"

    def test_raises_error_for_unsupported_mime_type(self) -> None:
        """サポートされていないMIMEタイプの場合、エラーを発生させる."""
        # Act & Assert
        with pytest.raises(ErrInvalidImageExtension) as exc_info:
            mime_type_to_extension("image/webp")

        assert "Unsupported MIME type" in str(exc_info.value)
        assert "image/webp" in str(exc_info.value)

    def test_raises_error_for_invalid_mime_type(self) -> None:
        """無効なMIMEタイプの場合、エラーを発生させる."""
        # Act & Assert
        with pytest.raises(ErrInvalidImageExtension) as exc_info:
            mime_type_to_extension("application/pdf")

        assert "Unsupported MIME type" in str(exc_info.value)

    def test_convert_uppercase_mime_type(self) -> None:
        """大文字のMIMEタイプも正しく変換される(大文字小文字を区別しない)."""
        # Act
        result = mime_type_to_extension("IMAGE/JPEG")

        # Assert
        assert result == ".jpg"

    def test_convert_mixed_case_mime_type(self) -> None:
        """混在した大文字小文字のMIMEタイプも正しく変換される."""
        # Act
        result = mime_type_to_extension("Image/Png")

        # Assert
        assert result == ".png"

    def test_convert_mime_type_with_whitespace(self) -> None:
        """前後に空白を含むMIMEタイプも正しく変換される(トリム処理)."""
        # Act
        result = mime_type_to_extension("  image/jpeg  ")

        # Assert
        assert result == ".jpg"

    def test_convert_mime_type_uppercase_with_whitespace(self) -> None:
        """大文字と空白の両方を含むMIMEタイプも正しく変換される."""
        # Act
        result = mime_type_to_extension("  IMAGE/PNG  ")

        # Assert
        assert result == ".png"
