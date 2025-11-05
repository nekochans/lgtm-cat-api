# 絶対厳守：編集前に必ずAI実装ルールを読む
"""LgtmImageCreateFromUrlRequestのバリデーションテスト."""

import pytest
from pydantic import ValidationError

from presentation.controller.lgtm_image_request import (
    LgtmImageCreateFromUrlRequest,
)


class TestLgtmImageCreateFromUrlRequest:
    def test_valid_https_url(self) -> None:
        """正常系: 有効なHTTPS URLが受け入れられる."""
        # Arrange & Act
        request = LgtmImageCreateFromUrlRequest(
            imageUrl="https://example.com/image.png"
        )

        # Assert
        assert request.image_url == "https://example.com/image.png"

    def test_valid_https_url_with_query_params(self) -> None:
        """正常系: クエリパラメータ付きのHTTPS URLが受け入れられる."""
        # Arrange & Act
        request = LgtmImageCreateFromUrlRequest(
            imageUrl="https://bucket.s3.amazonaws.com/image.png?AWSAccessKeyId=XXX&Signature=YYY"
        )

        # Assert
        assert (
            request.image_url
            == "https://bucket.s3.amazonaws.com/image.png?AWSAccessKeyId=XXX&Signature=YYY"
        )

    def test_valid_https_url_with_path(self) -> None:
        """正常系: 複雑なパスを持つHTTPS URLが受け入れられる."""
        # Arrange & Act
        request = LgtmImageCreateFromUrlRequest(
            imageUrl="https://cdn.example.com/images/2025/01/test.jpg"
        )

        # Assert
        assert request.image_url == "https://cdn.example.com/images/2025/01/test.jpg"

    @pytest.mark.parametrize(
        "invalid_url,expected_error_msg",
        [
            ("http://example.com/image.png", "https URL"),
            ("ftp://example.com/image.png", "https URL"),
            ("file:///path/to/image.png", "https URL"),
            ("example.com/image.png", "https URL"),
        ],
        ids=["http-scheme", "ftp-scheme", "file-scheme", "no-scheme"],
    )
    def test_invalid_url_schemes(
        self, invalid_url: str, expected_error_msg: str
    ) -> None:
        """異常系: HTTPS以外のスキームのURLは拒否される."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            LgtmImageCreateFromUrlRequest(imageUrl=invalid_url)

        # バリデーションエラーの詳細を確認
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("imageUrl",)
        assert expected_error_msg in str(errors[0]["msg"])

    def test_invalid_no_hostname(self) -> None:
        """異常系: ホスト名のないURLは拒否される."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            LgtmImageCreateFromUrlRequest(imageUrl="https://")

        # バリデーションエラーの詳細を確認
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("imageUrl",)
        assert "valid hostname" in str(errors[0]["msg"])

    def test_invalid_not_url_format(self) -> None:
        """異常系: URL形式ではない文字列は拒否される."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            LgtmImageCreateFromUrlRequest(imageUrl="not-a-url")

        # バリデーションエラーの詳細を確認
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("imageUrl",)

    def test_invalid_empty_string(self) -> None:
        """異常系: 空文字列は拒否される."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            LgtmImageCreateFromUrlRequest(imageUrl="")

        # バリデーションエラーの詳細を確認
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("imageUrl",)
        # min_length=1の制約によってエラーになる
        assert "at least 1 character" in str(errors[0]["msg"])
