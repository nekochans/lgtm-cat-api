# 絶対厳守:編集前に必ずAI実装ルールを読む

from unittest.mock import MagicMock, patch

from sentry.initializer import capture_exception, init_sentry


class TestInitSentry:
    @patch("sentry.initializer.sentry_sdk")
    def test_init_sentry_with_valid_dsn_prod(self, mock_sentry_sdk: MagicMock) -> None:
        """本番環境で有効なDSNでSentryが初期化されること"""
        # Arrange
        dsn = "https://example@sentry.io/123456"
        environment = "production"

        # Act
        init_sentry(dsn, environment)

        # Assert
        mock_sentry_sdk.init.assert_called_once()
        call_args = mock_sentry_sdk.init.call_args
        assert call_args.kwargs["dsn"] == dsn
        assert call_args.kwargs["environment"] == environment
        assert call_args.kwargs["traces_sample_rate"] == 0.2
        assert call_args.kwargs["profiles_sample_rate"] == 0.1
        assert call_args.kwargs["send_default_pii"] is False

    @patch("sentry.initializer.sentry_sdk")
    def test_init_sentry_with_valid_dsn_non_production(
        self, mock_sentry_sdk: MagicMock
    ) -> None:
        """非本番環境で有効なDSNでSentryが初期化されること"""
        # Arrange
        dsn = "https://example@sentry.io/123456"
        environment = "staging"

        # Act
        init_sentry(dsn, environment)

        # Assert
        mock_sentry_sdk.init.assert_called_once()
        call_args = mock_sentry_sdk.init.call_args
        assert call_args.kwargs["dsn"] == dsn
        assert call_args.kwargs["environment"] == environment
        assert call_args.kwargs["traces_sample_rate"] == 0.05
        assert call_args.kwargs["profiles_sample_rate"] == 0.01
        assert call_args.kwargs["send_default_pii"] is False

    @patch("sentry.initializer.sentry_sdk")
    @patch("sentry.initializer.logger")
    def test_init_sentry_with_empty_dsn(
        self, mock_logger: MagicMock, mock_sentry_sdk: MagicMock
    ) -> None:
        """DSNが空の場合、Sentryが初期化されないこと"""
        # Arrange
        dsn = ""
        environment = "development"

        # Act
        init_sentry(dsn, environment)

        # Assert
        mock_sentry_sdk.init.assert_not_called()
        mock_logger.info.assert_called_once_with(
            "Sentry DSN is not set. Skipping Sentry initialization."
        )

    @patch("sentry.initializer.sentry_sdk")
    @patch("sentry.initializer.logger")
    def test_init_sentry_raises_exception_on_failure(
        self, mock_logger: MagicMock, mock_sentry_sdk: MagicMock
    ) -> None:
        """Sentry初期化失敗時に例外が再raiseされること"""
        # Arrange
        dsn = "https://example@sentry.io/123456"
        environment = "production"
        original_error = RuntimeError("Sentry initialization failed")
        mock_sentry_sdk.init.side_effect = original_error

        # Act & Assert
        try:
            init_sentry(dsn, environment)
            assert False, "Expected exception to be raised"
        except RuntimeError as e:
            assert e is original_error

        # エラーログが出力されることを確認
        mock_logger.error.assert_called_once_with(
            "Failed to initialize Sentry", exc_info=True
        )


class TestCaptureException:
    @patch("sentry.initializer.sentry_sdk")
    def test_capture_exception_without_extra(self, mock_sentry_sdk: MagicMock) -> None:
        """追加コンテキストなしで例外をキャプチャできること"""
        # Arrange
        error = RuntimeError("test error")

        # Act
        capture_exception(error)

        # Assert
        mock_sentry_sdk.capture_exception.assert_called_once_with(error)

    @patch("sentry.initializer.sentry_sdk")
    def test_capture_exception_with_extra(self, mock_sentry_sdk: MagicMock) -> None:
        """追加コンテキスト付きで例外をキャプチャできること"""
        # Arrange
        error = RuntimeError("test error")
        extra = {"request_id": "123", "user_id": "456"}
        mock_scope = MagicMock()
        mock_sentry_sdk.push_scope.return_value.__enter__.return_value = mock_scope

        # Act
        capture_exception(error, extra=extra)

        # Assert
        assert mock_scope.set_extra.call_count == 2
        mock_scope.set_extra.assert_any_call("request_id", "123")
        mock_scope.set_extra.assert_any_call("user_id", "456")
        mock_sentry_sdk.capture_exception.assert_called_once_with(error)
