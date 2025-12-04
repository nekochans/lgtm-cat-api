# 実行計画: Issue #84 - LGTMeow APIをMCP Serverとして公開する

## Issue情報

- **Issue URL**: https://github.com/nekochans/lgtm-cat-api/issues/84
- **作成日**: 2025-12-01

## 概要

LGTMeow APIをMCP Serverとして一般公開し、各AIエージェントから利用できるようにする。`fastapi-mcp`ライブラリを使用して、特定のエンドポイントを認証なしでMCP経由でアクセス可能にする。

## 完了の定義（Issueより）

- [x] MCPクライアントから `GET /lgtm-images` を呼び出してランダムなLGTM画像を取得できる
- [x] MCPクライアントから `GET /lgtm-images/recently-created` を呼び出して最近作成されたLGTM画像を取得できる
- [x] 上記2つのエンドポイントはMCP経由では認証なしで利用可能

---

## 完了要件

### テスト要件

- [x] MCP専用ルーターの正常系テスト（`GET /lgtm-images` で認証なしで画像取得できること）
- [x] MCP専用ルーターの正常系テスト（`GET /lgtm-images/recently-created` で認証なしで画像取得できること）
- [x] レコード不足時の404エラーハンドリングテスト
- [x] 既存エンドポイントが従来通り動作すること（回帰テストは既存テストで担保済み）

### ドキュメント要件

- [x] README.mdにMCP Server機能の説明を追加

### 品質要件（固定）

- [x] `make lint` が通る
- [x] `make typecheck` が通る
- [x] `make test` が通る

---

## フェーズ構成

| フェーズ | 説明 | タスク数 |
|---------|------|---------|
| Phase 1 | MCP統合の実装 | 4 |

---

## Phase 1: MCP統合の実装

### 目的

`fastapi-mcp`を使用してMCP Serverとして公開し、認証なしでLGTM画像取得エンドポイントを提供する。

### タスク一覧

- [x] **Task 1.1**: pyproject.tomlに`fastapi-mcp`を追加
  - 対象ファイル: `pyproject.toml`
  - 作業内容: `dependencies`セクションに`fastapi-mcp`を追加し、`uv sync`を実行

- [x] **Task 1.2**: MCP専用ルーターを作成
  - 対象ファイル: `src/presentation/router/mcp_lgtm_image_router.py` (新規作成)
  - 作業内容:
    - 既存の`lgtm_image_router.py`の`GET /lgtm-images`と`GET /lgtm-images/recently-created`を参考に実装
    - 認証なし（`verify_token`依存を削除）
    - `tags=["mcp_tool"]`を付与
    - 同じコントローラーとユースケースを再利用

- [x] **Task 1.3**: main.pyにfastapi-mcp統合を追加
  - 対象ファイル: `src/main.py`
  - 作業内容:
    - `from fastapi_mcp import FastAPIMCP`をインポート
    - `FastAPIMCP(app, include_tags=["mcp_tool"])`でMCPを初期化
    - MCP専用ルーター（`mcp_lgtm_image_router`）を登録

- [x] **Task 1.4**: MCP専用ルーターのテストを作成
  - 対象ファイル: `tests/presentation/router/test_mcp_lgtm_image_router.py` (新規作成)
  - 作業内容:
    - **FastAPI TestClient**を使用したHTTPリクエストテスト
    - `test_db_session`を使用した実DBテスト
    - 正常系: 認証なしでHTTPリクエスト経由で画像を取得できることを確認
    - 異常系: レコード不足時に404を返すことを確認
  - テスト方法:
    - `httpx.AsyncClient`と`app`を使用（非同期テスト）
    - `client.get("/mcp/lgtm-images")` でエンドポイントパスへリクエスト
    - MCPルーターは `/mcp` prefixを持つため、既存の認証付きルーターと共存可能
    - Routerの依存性注入（`Depends`）が正しく動作することを確認

### 完了条件

- [x] MCPクライアントから認証なしで画像取得できる
- [x] 既存の認証付きエンドポイントは従来通り動作する
- [x] テストが追加され、すべてパスする
- [x] 品質チェックが通る

---

## 実装メモ

### 影響を受けるファイル

- `pyproject.toml` - `fastapi-mcp`依存を追加
- `src/presentation/router/mcp_lgtm_image_router.py` - MCP専用ルーター（新規作成）
- `src/main.py` - FastAPIMCP統合とルーター登録
- `tests/presentation/router/test_mcp_lgtm_image_router.py` - テスト（新規作成）

### 参考にすべき既存コード

- `src/presentation/router/lgtm_image_router.py` - 既存のLGTM画像ルーター（ルーターパターン）
- `src/presentation/controller/lgtm_image_controller.py` - 再利用するコントローラー
- `tests/fixtures/test_data_helpers.py` - テストデータ作成ヘルパー

### Routerテストの正しいパターン

Routerテストでは**FastAPI TestClient**または**httpx.AsyncClient**を使用してHTTPリクエストをテストする：

```python
import pytest
from httpx import ASGITransport, AsyncClient
from src.main import app

class TestMcpLgtmImageRouterRandomImages:
    @pytest.mark.asyncio
    async def test_get_random_lgtm_images_success(
        self, test_db_session, override_dependencies
    ):
        # DBにテストデータを挿入
        await insert_test_lgtm_images(test_db_session, count=20)

        # HTTPリクエストでエンドポイントをテスト（/mcp prefix）
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/mcp/lgtm-images")

        assert response.status_code == 200
        assert "lgtmImages" in response.json()
```

**注意**: Controllerを直接呼び出すのはControllerテスト。Routerテストは必ずHTTPリクエスト経由でテストする。

### 注意点

- **既存の認証付きエンドポイントには影響を与えない**
  - `lgtm_image_router.py`は一切変更しない
  - MCPルーターは別ファイルとして新規作成

- **コントローラーとユースケースは再利用**
  - `LgtmImageController.exec()`と`LgtmImageController.exec_recently_created()`をそのまま使用
  - 新しいコントローラーやユースケースは作成しない

- **fastapi-mcpの使い方**
  - 公式ドキュメントを参照して正しい初期化方法を確認
  - `include_tags=["mcp_tool"]`により、指定タグのエンドポイントのみMCP公開
  - **マウント方式**: `mount_sse()`を使用（SSE transport）
    - 公式ドキュメントでは`mount_http()`（Streamable HTTP）が推奨されている
    - しかし、AWS ECS + ALB環境では`mount_http()`が正常に動作しない問題が発生
      - `StreamableHTTPSessionManager`の非同期ストリーム読み取りがECS環境で動作しない
      - リクエストボディの読み取りでタイムアウトが発生する
    - `mount_sse()`はAWS環境との互換性が高く、安定して動作する
    - SSEモードのエンドポイント: `/sse`（デフォルト）

- **テストディレクトリの作成**
  - `tests/presentation/router/`ディレクトリを新規作成
  - `__init__.py`も忘れずに追加

- **品質チェック**
  - `make lint`, `make typecheck`, `make test`をすべて通過させる
  - 型アノテーションを正しく記述する

- **ミドルウェアの互換性問題**
  - fastapi-mcpのSSEエンドポイント（`/sse`）で「Unexpected ASGI message 'http.response.body'」エラーが発生
  - これは [tadata-org/fastapi_mcp#171](https://github.com/tadata-org/fastapi_mcp/issues/171) と同様の問題
  - **原因**: StarletteのBaseHTTPMiddlewareがSSEストリーミングと互換性がない
  - **対応**: LoggingMiddlewareとRequestIdMiddlewareを純粋なASGIミドルウェアとして再実装
  - **SSEエンドポイントのスキップ処理**:
    - LoggingMiddleware: SSEは長時間接続のため、通常のHTTPリクエストとログ出力の性質が異なる（処理時間が数分〜数時間になる）ためスキップ
    - RequestIdMiddleware: LoggingMiddlewareでログを出力しないため、リクエストIDを生成・設定する意味がないのでスキップ
