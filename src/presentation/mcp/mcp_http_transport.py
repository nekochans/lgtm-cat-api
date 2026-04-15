# 絶対厳守：編集前に必ずAI実装ルールを読む

"""MCP HTTPトランスポート実装.

StreamableHTTPSessionManagerを使用したMCPサーバーのHTTPトランスポート。
ASGIアプリとしてFastAPIの `/mcp` パスにマウントされます。
"""

from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from starlette.types import ASGIApp, Receive, Scope, Send

from config import get_mcp_allowed_hosts
from presentation.mcp.mcp_server import create_mcp_server

# StreamableHTTPSessionManagerを初期化
# DNS rebinding攻撃を防ぐため、許可されたホストのみを受け入れる
session_manager = StreamableHTTPSessionManager(
    create_mcp_server(),
    security_settings=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=get_mcp_allowed_hosts(),
        allowed_origins=[],  # MCPプロトコルではOriginチェック不要
    ),
)


class MCPHTTPApp:
    """StreamableHTTPSessionManagerをASGIアプリとしてラップするクラス."""

    def __init__(self, session_manager: StreamableHTTPSessionManager) -> None:
        self.session_manager = session_manager

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGIアプリケーションのエントリーポイント."""
        await self.session_manager.handle_request(scope, receive, send)


# ASGIアプリとしてエクスポート
http_app: ASGIApp = MCPHTTPApp(session_manager)
