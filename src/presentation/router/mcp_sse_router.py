# 絶対厳守:編集前に必ずAI実装ルールを読む

"""MCP SSEトランスポート用のルーター実装.

このモジュールはMCP (Model Context Protocol) サーバーのSSE (Server-Sent Events)
トランスポートを提供します。`/sse` パスで公開し、後方互換性を保ちます。

エンドポイント:
- GET /sse - SSEストリームの開始
- POST /messages/ - クライアントからのメッセージ受信（SSEセッションにリンク）
"""

from fastapi import APIRouter, Request
from fastapi.responses import Response
from mcp.server.sse import SseServerTransport
from mcp.server.transport_security import TransportSecuritySettings

from config import get_mcp_allowed_hosts
from presentation.mcp.mcp_server import create_mcp_server
from log.logger import get_logger

logger = get_logger(__name__)

# SSEトランスポート用のルーター
router = APIRouter()

# MCP Serverインスタンスを作成
server = create_mcp_server()

# SSEトランスポートを作成（メッセージ投稿先のエンドポイントを指定）
# DNS rebinding攻撃を防ぐため、許可されたホストのみを受け入れる
sse = SseServerTransport(
    "/sse/messages/",
    security_settings=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=get_mcp_allowed_hosts(),
        allowed_origins=[],  # MCPプロトコルではOriginチェック不要
    ),
)


@router.get("/sse", include_in_schema=False)
async def handle_sse(request: Request) -> Response:
    """SSE接続を処理するエンドポイント.

    このエンドポイントはMCPクライアントからのSSE接続を受け付け、
    サーバーからクライアントへのイベントストリームを確立します。

    Args:
        request: FastAPIリクエストオブジェクト

    Returns:
        Response: 空のレスポンス（接続終了後に返す）
    """
    logger.info("SSE connection established")

    try:
        # SSE接続を確立してMCP Serverを実行
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Error handling SSE connection: {e}")
        raise

    # 空のレスポンスを返してTypeError: 'NoneType' object is not callableを回避
    return Response()


# 注意: POSTメッセージハンドラは main.py で以下のようにマウントする必要があります:
# app.mount("/sse/messages/", sse.handle_post_message)
