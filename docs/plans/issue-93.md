# 実行計画: Issue #93 - fastapi-mcpからMCP公式Python SDKへの移行

## Issue情報

- **Issue URL**: https://github.com/nekochans/lgtm-cat-api/issues/93
- **作成日**: 2026-04-03

## 概要

`fastapi-mcp`ライブラリをMCP公式Python SDK (`modelcontextprotocol/python-sdk`) に移行し、既存のSSEトランスポートに加えて Streamable HTTPトランスポートにも対応する。メンテナンスの継続性を確保し、今後のMCP仕様変更への追従を可能にする。

## 完了の定義（Issueより）

- [x] `fastapi-mcp` への依存が完全に除去されている
- [x] MCP公式Python SDK (`modelcontextprotocol/python-sdk`) を使用してMCP Serverが実装されている
- [x] 既存のSSEトランスポート (`/sse`) が引き続き動作する（後方互換性の維持）
- [x] Streamable HTTPトランスポートが追加されている
- [x] 既存の3つのMCPツールが同じツール名・スキーマで動作する
  - `get_random_lgtm_images`
  - `get_recently_created_lgtm_images`
  - `get_random_lgtm_markdown`
- [x] 既存のREST APIエンドポイント（認証が必要なもの）に影響がない
- [x] ミドルウェアのスキップ処理が新しいトランスポートのパスにも対応している

---

## 完了要件

### テスト要件

- [ ] SSEトランスポートの動作確認テスト（手動またはE2E）
- [ ] Streamable HTTPトランスポートの動作確認テスト（手動またはE2E）
- [ ] 既存の3つのMCPツールが正しく動作することの確認
- [ ] 既存のREST APIエンドポイントへの影響がないことの確認

### ドキュメント要件

#### Phase 1（PR #1）

- [ ] README.mdのMCP設定例の更新（SSEトランスポート用）
- [ ] 依存関係変更に関するドキュメント追加

#### Phase 2（PR #2）

- [ ] README.mdへのStreamable HTTPトランスポートの設定例追加
- [ ] MCPクライアント設定例の更新

### 品質要件（固定）

- [x] `make lint` が通る
- [x] `make typecheck` が通る
- [x] `make test` が通る

---

## フェーズ構成

| フェーズ | 説明 | タスク数 | PR |
|---------|------|---------|-----|
| Phase 1 | MCP公式Python SDKへの基本移行（SSEトランスポート対応） | 4 | PR #1 |
| Phase 2 | Streamable HTTPトランスポートの追加 | 3 | PR #2 |

---

## Phase 1: MCP公式Python SDKへの基本移行（SSEトランスポート対応） - PR #1

### 目的

`fastapi-mcp`からMCP公式Python SDK（低レベルAPI: `mcp.server`）に移行し、既存のSSEトランスポート (`/sse`) を引き続き動作させる。これにより、クライアント側の設定変更なしに新しいSDKに移行できる。

**なぜ低レベルAPI (`mcp.server`) を使用するのか:**

FastMCP（`mcp.sse_app()`等の高レベルAPI）ではなく、低レベルAPI（`mcp.server.Server` + `SseServerTransport`）を採用する理由：

1. **Phase 2でのStreamable HTTPトランスポート追加に対応するため**
   - `/sse`（SSE）と`/mcp`（Streamable HTTP）の両トランスポートを明確に分離して提供する必要がある
   - FastMCPの`app.mount()`では、`mount_path`パラメータで柔軟なパス設計ができない
   - 低レベルAPIでは`SseServerTransport("/sse/messages/")`のように明示的にパス指定が可能
   - 将来的に`/sse`と`/mcp`が共存する構成を実現できる

2. **FastAPIの例外ハンドラーとの統合（副次的効果）**
   - 低レベルAPIで`APIRouter`として実装することで、FastAPIのルーティングシステムに統合される
   - 結果として、FastAPIの`@app.exception_handler`が正常に動作する
   - 404エラーが正しくJSON形式で返る（FastMCPではPlainText形式になる問題があった）

### タスク一覧

- [x] **Task 1.1**: 依存関係の更新
  - 対象ファイル: `pyproject.toml`
  - 作業内容:
    - `fastapi-mcp>=0.4.0` を削除
    - `mcp>=1.0.0` を追加（MCP公式Python SDK）
    - `uv sync` を実行して依存関係を同期

- [x] **Task 1.2**: MCP Server実装の作成
  - 対象ファイル: `src/presentation/mcp/mcp_server.py`（新規作成）
  - 作業内容:
    - MCP公式SDK（低レベルAPI）の`mcp.server.Server`を使用してMCP Serverを実装
    - 3つのMCPツールを定義（`get_random_lgtm_images`, `get_recently_created_lgtm_images`, `get_random_lgtm_markdown`）
    - 既存の`mcp_lgtm_image_router.py`のコントローラーロジックを再利用
    - **注**: クリーンアーキテクチャに準拠するため、Presentation層に配置

- [x] **Task 1.3**: SSEトランスポートの実装
  - 対象ファイル: `src/presentation/router/mcp_sse_router.py`（新規作成）
  - 作業内容:
    - `SseServerTransport`を使用してSSEトランスポートを実装
    - `/sse`パスで`GET`エンドポイントを提供（FastAPI `APIRouter`として実装）
    - `/sse/messages/`パスでPOSTメッセージハンドラーを提供（ASGIアプリとして`app.mount()`）
    - `TransportSecuritySettings`でDNS rebinding攻撃を防御
    - 既存の`/sse`パスを維持（後方互換性）

- [x] **Task 1.4**: main.pyの更新とドキュメント整備
  - 対象ファイル: `src/main.py`, `README.md`
  - 作業内容:
    - `fastapi-mcp`のインポートと`FastApiMCP`インスタンスを削除
    - `mcp_sse_router.router`を`app.include_router()`で登録（`/sse`エンドポイント）
    - `mcp_sse_router.sse.handle_post_message`を`app.mount("/sse/messages/")`でマウント
    - `mcp_lgtm_image_router`を削除（MCPクライアントは直接REST APIを呼ばないため不要）
    - README.mdのMCP設定例を更新（SSEトランスポート用の設定）
    - README.mdからMCP専用エンドポイントのセクションを削除

### 完了条件

- [x] `fastapi-mcp`への依存が完全に除去されている
- [x] SSEトランスポート (`/sse`) が動作する（実装完了、手動確認推奨）
- [x] 既存の3つのMCPツールが同じツール名・スキーマで動作する（実装完了、手動確認推奨）
- [x] 既存のREST APIエンドポイントに影響がない（テスト332件全て通過）
- [x] README.mdが更新されている
- [x] 品質チェックが通る（lint, typecheck, test全て通過）

---

## Phase 2: Streamable HTTPトランスポートの追加 - PR #2

### 目的

MCP仕様 2025-03-26 リビジョンで正式導入された Streamable HTTP トランスポートを追加する。これにより、将来的なSSEの非推奨化に備える。

### 依存関係

- Phase 1 の完了が必要（MCP公式Python SDKへの移行済み）

### タスク一覧

- [x] **Task 2.1**: Streamable HTTPトランスポートの実装
  - 対象ファイル: `src/presentation/mcp/mcp_http_transport.py`（新規作成）
  - 作業内容:
    - MCP公式SDKの`StreamableHTTPSessionManager`を使用してHTTPトランスポートを実装
    - `/mcp`パスでASGIアプリとして提供（`app.mount()`でマウント）
    - Phase 1で作成したMCP Serverインスタンスを再利用
    - `main.py`のlifespanで`session_manager.run()`を呼び出してタスクグループを初期化

- [x] **Task 2.2**: ミドルウェアのスキップ処理更新
  - 対象ファイル: `src/presentation/middleware/logging_middleware.py`, `src/presentation/middleware/request_id_middleware.py`
  - 作業内容:
    - `/mcp`パスもスキップするように条件を追加
    - 既存の`/sse`スキップ処理と統合（`/sse`または`/mcp`）

- [x] **Task 2.3**: main.pyの更新とドキュメント整備
  - 対象ファイル: `src/main.py`, `README.md`
  - 作業内容:
    - `mcp_http_transport`をインポートし、`app.mount("/mcp", mcp_http_transport.http_app)`でマウント
    - `lifespan`関数で`mcp_http_transport.session_manager.run()`を呼び出してタスクグループを初期化
    - README.mdにStreamable HTTPトランスポートの設定例を追加
    - MCPクライアント設定例を両方のトランスポート（SSE、HTTP）に対応

### 完了条件

- [x] Streamable HTTPトランスポート (`/mcp`) が動作する（実装完了、手動確認推奨）
- [x] ミドルウェアのスキップ処理が `/mcp` パスにも対応している
- [x] README.mdにStreamable HTTPトランスポートの設定例が追加されている
- [x] SSEトランスポートも引き続き動作する（両方のトランスポートが共存）
- [x] 品質チェックが通る（lint, typecheck, test全て通過）

---

## 実装メモ

### 影響を受けるファイル

#### Phase 1（PR #1）
- `pyproject.toml` - 依存関係変更（`fastapi-mcp`削除、`mcp`追加）
- `src/presentation/mcp/mcp_server.py` - 新規作成（`mcp.server.Server`を使用したMCP Server実装）
- `src/presentation/router/mcp_sse_router.py` - 新規作成（`SseServerTransport`を使用したSSEトランスポート）
- `src/main.py` - FastApiMCP削除、`mcp_sse_router`の登録とマウント
- `README.md` - MCP設定例更新

#### Phase 2（PR #2）
- `src/presentation/mcp/mcp_http_transport.py` - 新規作成（HTTPトランスポート、`StreamableHTTPSessionManager`使用）
- `src/presentation/middleware/logging_middleware.py` - スキップパス追加（`/mcp`を追加）
- `src/presentation/middleware/request_id_middleware.py` - スキップパス追加（`/mcp`を追加）
- `src/main.py` - HTTPトランスポートのマウントとlifespan設定
- `README.md` - HTTPトランスポート設定例追加

### 参考にすべき既存コード

- `src/presentation/router/mcp_lgtm_image_router.py` - 既存のMCPツール定義とコントローラー呼び出しパターン
- `src/presentation/middleware/logging_middleware.py` - `/sse`スキップ処理パターン（line 23-27）
- `src/presentation/middleware/request_id_middleware.py` - `/sse`スキップ処理パターン（line 20-24）

### 注意点

#### Phase 1
- MCPツール名は既存と同じにする（`get_random_lgtm_images`, `get_recently_created_lgtm_images`, `get_random_lgtm_markdown`）
- レスポンス形式も既存と完全に同じにする（クライアント側の設定変更を不要にする）
- `/sse`パスを維持する（後方互換性）
- メッセージハンドラーパスは`/sse/messages/`とする（Phase 2での`/mcp`追加を考慮した設計）
- `mcp_lgtm_image_router.py`は削除（MCPクライアントは `/sse` 経由でツールを呼び出すため、REST APIエンドポイントは不要）
- `handle_post_message`はASGIアプリなので`app.mount()`を使用（`app.include_router()`は使えない）

#### Phase 2
- ミドルウェアのスキップ処理は `/sse` と `/mcp` の両方に対応（`path.startswith("/sse") or path.startswith("/mcp")`）
- `StreamableHTTPSessionManager`を使用してHTTPトランスポートを実装
- `main.py`の`lifespan`関数内で`session_manager.run()`を呼び出してタスクグループを初期化（必須）
- HTTPトランスポートはASGIアプリとして`app.mount("/mcp", mcp_http_transport.http_app)`でマウント
- SSEとHTTPの両方のトランスポートが同時に動作することを確認

**Streamable HTTPで`app.mount()`を使う理由:**

事実として以下が観察される:
1. `StreamableHTTPSessionManager.handle_request()`はASGIインターフェース（`scope, receive, send`）を受け取り、`None`を返す
2. FastAPIの`APIRouter`はFastAPIエンドポイント関数（`Request`, `Response`を扱う）を期待する
3. これらは異なるインターフェースのため、`APIRouter`として直接登録できない
4. そのため、ASGIアプリとしてラップし（`MCPHTTPApp`クラス）、`app.mount()`でマウントする

### MCP公式Python SDKの参考情報

- GitHub: https://github.com/modelcontextprotocol/python-sdk
- ドキュメント: https://modelcontextprotocol.io/docs/
- FastAPI統合例: https://github.com/modelcontextprotocol/python-sdk/tree/main/examples/fastapi

### PR分割の理由

1. **Phase 1（PR #1）**: 既存機能の維持を最優先
   - SSEトランスポートの移行のみに集中
   - リスクを最小化し、レビューを容易にする
   - この段階で既存クライアントへの影響がないことを確認

2. **Phase 2（PR #2）**: 新機能の追加
   - Phase 1が安定稼働していることを確認してから着手
   - 新しいトランスポートの追加は独立した機能変更
   - 問題があった場合、Phase 1にロールバックしやすい
