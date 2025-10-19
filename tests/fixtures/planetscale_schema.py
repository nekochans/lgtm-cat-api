# 絶対厳守：編集前に必ずAI実装ルールを読む

import os

import aiohttp

# スキーマのキャッシュ（グローバル変数）
_schema_cache: dict[str, str] | None = None


async def get_planetscale_schema() -> dict[str, str]:
    """PlanetScale APIからスキーマを取得してキャッシュする.

    Returns:
        テーブル名をキーとし、CREATE TABLE文を値とする辞書

    Raises:
        ValueError: 必要な環境変数が設定されていない場合
        aiohttp.ClientError: API呼び出しに失敗した場合
    """
    global _schema_cache

    # キャッシュがあればそれを返す
    if _schema_cache is not None:
        return _schema_cache

    # 環境変数の取得
    org_name = os.getenv("PLANETSCALE_ORG_NAME")
    if org_name is None:
        raise ValueError("PLANETSCALE_ORG_NAME environment variable is not set")

    service_token_id = os.getenv("PLANETSCALE_SERVICE_TOKEN_ID")
    if service_token_id is None:
        raise ValueError("PLANETSCALE_SERVICE_TOKEN_ID environment variable is not set")

    service_token = os.getenv("PLANETSCALE_SERVICE_TOKEN")
    if service_token is None:
        raise ValueError("PLANETSCALE_SERVICE_TOKEN environment variable is not set")

    database_name = os.getenv("PLANETSCALE_DATABASE_NAME")
    if database_name is None:
        raise ValueError("PLANETSCALE_DATABASE_NAME environment variable is not set")

    branch_name = os.getenv("PLANETSCALE_BRANCH_NAME")
    if branch_name is None:
        raise ValueError("PLANETSCALE_BRANCH_NAME environment variable is not set")

    # PlanetScale API URL
    url = (
        f"https://api.planetscale.com/v1/organizations/{org_name}"
        f"/databases/{database_name}/branches/{branch_name}/schema"
    )

    # Authorizationヘッダーの設定
    headers = {"Authorization": f"{service_token_id}:{service_token}"}

    # APIリクエスト
    async with aiohttp.ClientSession() as session:
        timeout = aiohttp.ClientTimeout(total=30)
        async with session.get(url, headers=headers, timeout=timeout) as response:
            response.raise_for_status()
            data = await response.json()

    # レスポンスに'data'キーが存在するかチェック
    if "data" not in data:
        # errorフィールドがあればそれを、なければレスポンス全体を含める
        error_info = data.get("error", data)
        raise ValueError(
            f"Response missing required 'data' key. Response: {error_info}"
        )

    schema_data = data["data"]

    # PlanetScale APIは常にリストを返す
    if not isinstance(schema_data, list):
        raise ValueError(
            f"Unexpected response format: 'data' should be a list, got {type(schema_data).__name__}"
        )

    tables = schema_data

    # スキーマ情報を辞書形式で作成
    schema_dict: dict[str, str] = {}
    for table in tables:
        table_name = table.get("name", "")
        # PlanetScale APIは 'raw' キーでCREATE TABLE文を返す
        create_statement = table.get("raw", "")
        if table_name and create_statement:
            # 先頭と末尾の空白を除去（内部の改行やコメントは保持）
            cleaned_statement = create_statement.strip()
            schema_dict[table_name] = cleaned_statement

    # キャッシュに保存
    _schema_cache = schema_dict

    return schema_dict
