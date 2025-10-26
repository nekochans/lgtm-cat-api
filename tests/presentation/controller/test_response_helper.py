# 絶対厳守:編集前に必ずAI実装ルールを読む

from unittest.mock import MagicMock, patch

from presentation.controller.response_helper import create_error_response


class TestHandleInternalError:
    @patch("presentation.controller.response_helper.get_request_id")
    @patch("presentation.controller.response_helper.capture_exception")
    def test_returns_500_json_response(
        self,
        mock_capture_exception: MagicMock,
        mock_get_request_id: MagicMock,
    ) -> None:
        """500ステータスコードのJSONResponseを返すこと"""
        # Arrange
        error = RuntimeError("test error")
        mock_get_request_id.return_value = None

        # Act
        response = create_error_response(error)

        # Assert
        assert response.status_code == 500
        assert response.body == b'{"error":"Internal server error"}'

    @patch("presentation.controller.response_helper.get_request_id")
    @patch("presentation.controller.response_helper.capture_exception")
    def test_captures_exception_without_extra_and_without_request_id(
        self,
        mock_capture_exception: MagicMock,
        mock_get_request_id: MagicMock,
    ) -> None:
        """追加コンテキストなし、request_idなしでSentryに例外を送信すること"""
        # Arrange
        error = RuntimeError("test error")
        mock_get_request_id.return_value = None

        # Act
        create_error_response(error)

        # Assert
        mock_capture_exception.assert_called_once_with(error, extra=None)

    @patch("presentation.controller.response_helper.get_request_id")
    @patch("presentation.controller.response_helper.capture_exception")
    def test_captures_exception_with_extra(
        self,
        mock_capture_exception: MagicMock,
        mock_get_request_id: MagicMock,
    ) -> None:
        """追加コンテキスト付きでSentryに例外を送信すること"""
        # Arrange
        error = RuntimeError("test error")
        extra = {"user_id": "123", "action": "create_image"}
        mock_get_request_id.return_value = None

        # Act
        create_error_response(error, extra=extra)

        # Assert
        mock_capture_exception.assert_called_once_with(error, extra=extra)

    @patch("presentation.controller.response_helper.get_request_id")
    @patch("presentation.controller.response_helper.capture_exception")
    def test_captures_exception_with_request_id(
        self,
        mock_capture_exception: MagicMock,
        mock_get_request_id: MagicMock,
    ) -> None:
        """request_idが存在する場合、コンテキストに追加してSentryに送信すること"""
        # Arrange
        error = RuntimeError("test error")
        mock_get_request_id.return_value = "test-request-id-123"

        # Act
        create_error_response(error)

        # Assert
        mock_capture_exception.assert_called_once_with(
            error, extra={"request_id": "test-request-id-123"}
        )

    @patch("presentation.controller.response_helper.get_request_id")
    @patch("presentation.controller.response_helper.capture_exception")
    def test_captures_exception_with_extra_and_request_id(
        self,
        mock_capture_exception: MagicMock,
        mock_get_request_id: MagicMock,
    ) -> None:
        """追加コンテキストとrequest_idの両方が存在する場合、マージしてSentryに送信すること"""
        # Arrange
        error = RuntimeError("test error")
        extra = {"user_id": "123", "action": "create_image"}
        mock_get_request_id.return_value = "test-request-id-456"

        # Act
        create_error_response(error, extra=extra)

        # Assert
        mock_capture_exception.assert_called_once_with(
            error,
            extra={
                "user_id": "123",
                "action": "create_image",
                "request_id": "test-request-id-456",
            },
        )
