# 絶対厳守：編集前に必ずAI実装ルールを読む

"""MCP公式Python SDK (FastMCP) を使用したMCP Server実装.

このモジュールはLGTM猫画像を取得するための3つのツールを持つ
MCP (Model Context Protocol) サーバー機能を提供します。
REST APIとの一貫性を保つため、既存のコントローラーロジックを再利用します。

ツール:
- get_random_lgtm_images: ランダムに選択されたLGTM画像のリストを取得
- get_recently_created_lgtm_images: 最近作成されたLGTM画像のリストを取得
- get_random_lgtm_markdown: ランダムなLGTM画像をMarkdown形式で取得
"""

import json
from typing import Any, cast

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from config import get_lgtm_images_base_url, get_lgtmeow_url, get_mcp_allowed_hosts
from domain.repository.lgtm_image_repository_interface import (
    LgtmImageRepositoryInterface,
)
from infrastructure.database import AsyncSessionLocal
from infrastructure.lgtm_image_repository import LgtmImageRepository
from log.logger import get_logger
from presentation.controller.lgtm_image_controller import LgtmImageController

logger = get_logger(__name__)

# FastMCPインスタンスを作成
mcp = FastMCP(
    "lgtmeow",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=get_mcp_allowed_hosts(),
        allowed_origins=[],  # MCPプロトコルではOriginチェック不要
    ),
)


@mcp.tool()
async def get_random_lgtm_images() -> dict[str, Any]:
    """ランダムに選択されたLGTM画像のリストを取得する.

    Returns:
        dict[str, Any]: LGTM画像のリストを含む辞書
    """
    logger.info("Executing MCP tool: get_random_lgtm_images")

    async with AsyncSessionLocal() as session:
        repository: LgtmImageRepositoryInterface = LgtmImageRepository(session)
        base_url = get_lgtm_images_base_url()

        response = await LgtmImageController.exec(repository, base_url)
        # JSONResponseからJSONデータを抽出
        body = (
            response.body if isinstance(response.body, bytes) else bytes(response.body)
        )
        return cast(dict[str, Any], json.loads(body.decode("utf-8")))


@mcp.tool()
async def get_recently_created_lgtm_images() -> dict[str, Any]:
    """最近作成されたLGTM画像のリストを取得する.

    Returns:
        dict[str, Any]: LGTM画像のリストを含む辞書
    """
    logger.info("Executing MCP tool: get_recently_created_lgtm_images")

    async with AsyncSessionLocal() as session:
        repository: LgtmImageRepositoryInterface = LgtmImageRepository(session)
        base_url = get_lgtm_images_base_url()

        response = await LgtmImageController.exec_recently_created(repository, base_url)
        # JSONResponseからJSONデータを抽出
        body = (
            response.body if isinstance(response.body, bytes) else bytes(response.body)
        )
        return cast(dict[str, Any], json.loads(body.decode("utf-8")))


@mcp.tool()
async def get_random_lgtm_markdown() -> dict[str, Any]:
    """ランダムなLGTM画像をMarkdown形式で取得する.

    Returns:
        dict[str, Any]: Markdown形式のLGTM画像を含む辞書
    """
    logger.info("Executing MCP tool: get_random_lgtm_markdown")

    async with AsyncSessionLocal() as session:
        repository: LgtmImageRepositoryInterface = LgtmImageRepository(session)
        base_url = get_lgtm_images_base_url()
        lgtmeow_url = get_lgtmeow_url()

        response = await LgtmImageController.exec_random_markdown(
            repository, base_url, lgtmeow_url
        )
        # JSONResponseからJSONデータを抽出
        body = (
            response.body if isinstance(response.body, bytes) else bytes(response.body)
        )
        return cast(dict[str, Any], json.loads(body.decode("utf-8")))
