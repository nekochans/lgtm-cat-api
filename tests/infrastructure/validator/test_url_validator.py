# 絶対厳守:編集前に必ずAI実装ルールを読む
"""URL検証ロジックのテスト."""

import pytest

from domain.lgtm_image_errors import ErrInvalidUrl
from infrastructure.validator.url_validator import validate_allowed_domain


class TestValidateUrlForSsrf:
    """validate_allowed_domain関数のテストクラス（許可されたドメインの署名付きURL専用）."""

    # テスト用の許可ドメイン
    ALLOWED_DOMAIN = "test-bucket.r2.cloudflarestorage.com"

    # ===== 正常系テスト =====

    def test_valid_signed_url(self) -> None:
        """許可されたドメインの署名付きURLは検証を通過する."""
        # Arrange
        url = f"https://{self.ALLOWED_DOMAIN}/path/to/image.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256"

        # Act & Assert - 例外が発生しないことを確認
        validate_allowed_domain(url, self.ALLOWED_DOMAIN)

    def test_valid_url_with_query_params(self) -> None:
        """クエリパラメータを含むURLは検証を通過する."""
        # Arrange
        url = f"https://{self.ALLOWED_DOMAIN}/image.webp?X-Amz-Credential=XXX&X-Amz-Signature=YYY"

        # Act & Assert - 例外が発生しないことを確認
        validate_allowed_domain(url, self.ALLOWED_DOMAIN)

    def test_valid_url_with_subdirectory(self) -> None:
        """サブディレクトリを含むURLは検証を通過する."""
        # Arrange
        url = f"https://{self.ALLOWED_DOMAIN}/uploads/2024/01/image.png?X-Amz-Algorithm=AWS4-HMAC-SHA256"

        # Act & Assert - 例外が発生しないことを確認
        validate_allowed_domain(url, self.ALLOWED_DOMAIN)

    # ===== 入力値検証テスト =====

    def test_empty_string_raises_error(self) -> None:
        """空文字列はエラーを発生させる."""
        # Arrange
        url = ""

        # Act & Assert
        with pytest.raises(ErrInvalidUrl) as exc_info:
            validate_allowed_domain(url, self.ALLOWED_DOMAIN)

        assert "URL must be a non-empty string" in str(exc_info.value)

    def test_none_raises_error(self) -> None:
        """Noneはエラーを発生させる."""
        # Arrange
        url = None

        # Act & Assert
        with pytest.raises(ErrInvalidUrl) as exc_info:
            validate_allowed_domain(url, self.ALLOWED_DOMAIN)  # type: ignore[arg-type]

        assert "URL must be a non-empty string" in str(exc_info.value)

    def test_url_without_hostname_raises_error(self) -> None:
        """ホスト名がないURLはエラーを発生させる."""
        # Arrange
        url = "https:///path/to/image.jpg"

        # Act & Assert
        with pytest.raises(ErrInvalidUrl) as exc_info:
            validate_allowed_domain(url, self.ALLOWED_DOMAIN)

        assert "URL must contain a valid hostname" in str(exc_info.value)

    def test_empty_allowed_domain_raises_error(self) -> None:
        """allowed_domainが空の場合はエラーを発生させる."""
        # Arrange
        url = f"https://{self.ALLOWED_DOMAIN}/image.jpg"

        # Act & Assert
        with pytest.raises(ErrInvalidUrl) as exc_info:
            validate_allowed_domain(url, "")

        assert "Allowed domain is not configured" in str(exc_info.value)

    def test_whitespace_only_allowed_domain_raises_error(self) -> None:
        """allowed_domainが空白のみの場合はエラーを発生させる."""
        # Arrange
        url = f"https://{self.ALLOWED_DOMAIN}/image.jpg"

        # Act & Assert
        with pytest.raises(ErrInvalidUrl) as exc_info:
            validate_allowed_domain(url, "   ")

        assert "Allowed domain is not configured" in str(exc_info.value)

    def test_non_string_allowed_domain_raises_error(self) -> None:
        """allowed_domainが文字列でない場合はエラーを発生させる."""
        # Arrange
        url = f"https://{self.ALLOWED_DOMAIN}/image.jpg"

        # Act & Assert
        with pytest.raises(ErrInvalidUrl) as exc_info:
            validate_allowed_domain(url, None)  # type: ignore[arg-type]

        assert "Allowed domain is not configured" in str(exc_info.value)

    # ===== スキーム検証テスト（パラメータ化） =====

    @pytest.mark.parametrize(
        "url,expected_scheme",
        [
            (f"http://{ALLOWED_DOMAIN}/image.png", "http"),
            (f"ftp://{ALLOWED_DOMAIN}/image.jpg", "ftp"),
            ("file:///etc/passwd", "file"),
        ],
    )
    def test_invalid_schemes_raise_error(self, url: str, expected_scheme: str) -> None:
        """HTTPS以外のスキームは拒否される."""
        # Act & Assert
        with pytest.raises(ErrInvalidUrl) as exc_info:
            validate_allowed_domain(url, self.ALLOWED_DOMAIN)

        assert f"Invalid URL scheme: {expected_scheme}" in str(exc_info.value)
        assert "Only https is allowed" in str(exc_info.value)

    # ===== ドメイン検証テスト =====

    @pytest.mark.parametrize(
        "url,description",
        [
            ("https://www.google.com/image.jpg", "Google (パブリックドメイン)"),
            ("https://s3.amazonaws.com/bucket/image.jpg", "AWS S3"),
            ("https://storage.googleapis.com/bucket/image.jpg", "Google Cloud Storage"),
            (
                "https://different-bucket.r2.cloudflarestorage.com/image.jpg",
                "異なるバケット",
            ),
            ("https://localhost:8000/image.jpg", "localhost"),
            ("https://127.0.0.1/image.jpg", "ループバックIP"),
            ("https://192.168.1.1/image.jpg", "プライベートIP"),
            ("https://10.0.0.1/image.jpg", "プライベートIP"),
            (
                "https://169.254.169.254/latest/meta-data/",
                "AWSメタデータエンドポイント",
            ),
        ],
    )
    def test_non_allowed_domains_raise_error(self, url: str, description: str) -> None:
        """許可されたドメイン以外のURLはすべて拒否される.

        SSRF攻撃を防ぐため、明示的に許可されたドメインのみを受け入れる。
        """
        # Act & Assert
        with pytest.raises(ErrInvalidUrl) as exc_info:
            validate_allowed_domain(url, self.ALLOWED_DOMAIN)

        error_message = str(exc_info.value)
        assert "is not allowed" in error_message
        assert self.ALLOWED_DOMAIN in error_message

    # ===== エッジケース =====

    def test_domain_case_insensitive(self) -> None:
        """ドメイン名の大文字小文字は自動的に正規化される（大文字で指定しても許可される）."""
        # Arrange
        url = f"https://{self.ALLOWED_DOMAIN.upper()}/image.jpg"

        # Act & Assert - URLパーサーが自動的に小文字化するため、検証を通過する
        validate_allowed_domain(url, self.ALLOWED_DOMAIN)

    def test_allowed_domain_with_uppercase_letters(self) -> None:
        """allowed_domainに大文字が含まれていても正しく検証される（大文字小文字を区別しない比較）."""
        # Arrange
        url = f"https://{self.ALLOWED_DOMAIN}/image.jpg"
        allowed_domain_with_uppercase = "Test-Bucket.R2.CloudflareStorage.COM"

        # Act & Assert - allowed_domainに大文字が含まれていても検証を通過する
        validate_allowed_domain(url, allowed_domain_with_uppercase)

    def test_domain_with_port_is_allowed(self) -> None:
        """ポート番号を含むドメインも許可される（hostnameは同じ）."""
        # Arrange - ポート番号があってもhostnameは同じなので許可される
        url = f"https://{self.ALLOWED_DOMAIN}:443/image.jpg"

        # Act & Assert - 例外が発生しないことを確認
        validate_allowed_domain(url, self.ALLOWED_DOMAIN)

    def test_subdomain_of_allowed_domain_raises_error(self) -> None:
        """許可されたドメインのサブドメインでも拒否される（完全一致のみ）."""
        # Arrange
        url = f"https://sub.{self.ALLOWED_DOMAIN}/image.jpg"

        # Act & Assert
        with pytest.raises(ErrInvalidUrl) as exc_info:
            validate_allowed_domain(url, self.ALLOWED_DOMAIN)

        assert "is not allowed" in str(exc_info.value)
