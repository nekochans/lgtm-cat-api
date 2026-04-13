# 絶対厳守：編集前に必ずAI実装ルールを読む

"""MCP公式Python SDKを使用したMCP Server実装.

このモジュールはLGTM猫画像を取得するための3つのツールを持つ
MCP (Model Context Protocol) サーバー機能を提供します。
REST APIとの一貫性を保つため、既存のコントローラーロジックを再利用します。

ツール:
- get_random_lgtm_images: ランダムに選択されたLGTM画像のリストを取得
- get_recently_created_lgtm_images: 最近作成されたLGTM画像のリストを取得
- get_random_lgtm_markdown: ランダムなLGTM画像をMarkdown形式で取得
"""

from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from config import get_lgtm_images_base_url, get_lgtmeow_url
from infrastructure.database import AsyncSessionLocal
from infrastructure.factory import create_lgtm_image_repository
from log.logger import get_logger
from presentation.controller.lgtm_image_controller import LgtmImageController

logger = get_logger(__name__)


def create_mcp_server() -> Server:
    """MCP Serverインスタンスを作成して設定する.

    Returns:
        Server: ツールハンドラが設定されたMCP Server
    """
    server = Server("lgtmeow")

    @server.list_tools()  # type: ignore[misc, no-untyped-call]  # MCP SDKのデコレーターに型定義がない
    async def list_tools() -> list[Tool]:
        """利用可能な全MCPツールのリストを返す.

        Returns:
            list[Tool]: スキーマを含む利用可能なツールのリスト
        """
        return [
            Tool(
                name="get_random_lgtm_images",
                description="Returns a list of randomly selected LGTM (Looks Good To Me) cat images for use in code review comments and pull request approvals.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            Tool(
                name="get_recently_created_lgtm_images",
                description="Returns a list of the most recently created LGTM (Looks Good To Me) cat images for use in code review comments and pull request approvals.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            Tool(
                name="get_random_lgtm_markdown",
                description="Returns a single randomly selected LGTM (Looks Good To Me) cat image in markdown format for use in code review comments and pull request approvals.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
        ]

    @server.call_tool()  # type: ignore[misc]  # MCP SDKのデコレーターに型定義がない
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """指定された名前のツールを実行する.

        Args:
            name: 実行するツール名
            arguments: ツールの引数（現在は全ツールがパラメータ不要のため未使用）

        Returns:
            list[TextContent]: テキストコンテンツとしてのツール実行結果
        """
        logger.info(f"Executing MCP tool: {name}")

        # データベースセッションとリポジトリを作成
        async with AsyncSessionLocal() as session:
            repository = create_lgtm_image_repository(session)
            base_url = get_lgtm_images_base_url()

            try:
                if name == "get_random_lgtm_images":
                    # ランダムなLGTM画像を取得
                    response = await LgtmImageController.exec(repository, base_url)
                    # JSONResponseからJSONコンテンツを抽出（response.bodyはbytes型）
                    body = (
                        response.body
                        if isinstance(response.body, bytes)
                        else bytes(response.body)
                    )
                    return [TextContent(type="text", text=body.decode("utf-8"))]

                elif name == "get_recently_created_lgtm_images":
                    # 最近作成されたLGTM画像を取得
                    response = await LgtmImageController.exec_recently_created(
                        repository, base_url
                    )
                    body = (
                        response.body
                        if isinstance(response.body, bytes)
                        else bytes(response.body)
                    )
                    return [TextContent(type="text", text=body.decode("utf-8"))]

                elif name == "get_random_lgtm_markdown":
                    # ランダムなLGTM画像をMarkdown形式で取得
                    lgtmeow_url = get_lgtmeow_url()
                    response = await LgtmImageController.exec_random_markdown(
                        repository, base_url, lgtmeow_url
                    )
                    body = (
                        response.body
                        if isinstance(response.body, bytes)
                        else bytes(response.body)
                    )
                    return [TextContent(type="text", text=body.decode("utf-8"))]

                else:
                    error_msg = f"Unknown tool: {name}"
                    logger.error(error_msg)
                    return [
                        TextContent(type="text", text=f'{{"error": "{error_msg}"}}')
                    ]

            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [
                    TextContent(type="text", text='{"error": "Internal server error"}')
                ]

    return server
