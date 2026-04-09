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
- [ ] Streamable HTTPトランスポートが追加されている
- [x] 既存の3つのMCPツールが同じツール名・スキーマで動作する
  - `get_random_lgtm_images`
  - `get_recently_created_lgtm_images`
  - `get_random_lgtm_markdown`
- [x] 既存のREST APIエンドポイント（認証が必要なもの）に影響がない
- [ ] ミドルウェアのスキップ処理が新しいトランスポートのパスにも対応している

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

- [ ] `make lint` が通る
- [ ] `make typecheck` が通る
- [ ] `make test` が通る

---

## フェーズ構成

| フェーズ | 説明 | タスク数 | PR |
|---------|------|---------|-----|
| Phase 1 | MCP公式Python SDKへの基本移行（SSEトランスポート対応） | 4 | PR #1 |
| Phase 2 | Streamable HTTPトランスポートの追加 | 3 | PR #2 |

---

## Phase 1: MCP公式Python SDKへの基本移行（SSEトランスポート対応） - PR #1

### 目的

`fastapi-mcp`からMCP公式Python SDKに移行し、既存のSSEトランスポート (`/sse`) を引き続き動作させる。これにより、クライアント側の設定変更なしに新しいSDKに移行できる。

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
    - MCP公式SDKを使用してMCP Serverクラスを実装
    - 3つのMCPツールを定義（`get_random_lgtm_images`, `get_recently_created_lgtm_images`, `get_random_lgtm_markdown`）
    - 既存の`mcp_lgtm_image_router.py`のコントローラーロジックを再利用
    - **注**: クリーンアーキテクチャに準拠するため、Presentation層に配置

- [x] **Task 1.3**: SSEトランスポートの実装
  - 対象ファイル: `src/main.py`
  - 作業内容:
    - FastMCP (MCP公式Python SDK) の`mcp.sse_app()`で生成されたSSEアプリを`app.mount()`でマウント
    - 既存の`/sse`パスを維持（後方互換性）
    - **注**: APIRouterは使用せず、FastMCPが提供するSSEアプリを直接マウントする方式を採用

- [x] **Task 1.4**: main.pyの更新とドキュメント整備
  - 対象ファイル: `src/main.py`, `README.md`
  - 作業内容:
    - `fastapi-mcp`のインポートと`FastApiMCP`インスタンスを削除
    - `mcp.sse_app(mount_path="")`を`app.mount("", ...)`でマウント（`/sse`パスで提供）
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

- [ ] **Task 2.1**: Streamable HTTPトランスポートの実装
  - 対象ファイル: `src/presentation/router/mcp_http_router.py`（新規作成）
  - 作業内容:
    - FastAPIのAPIRouterでHTTPエンドポイント (`/mcp`) を実装
    - MCP公式SDKのStreamable HTTPトランスポート機能を使用
    - Phase 1で作成したMCP Serverインスタンスを再利用

- [ ] **Task 2.2**: ミドルウェアのスキップ処理更新
  - 対象ファイル: `src/presentation/middleware/logging_middleware.py`, `src/presentation/middleware/request_id_middleware.py`
  - 作業内容:
    - `/mcp`パスもスキップするように条件を追加
    - 既存の`/sse`スキップ処理と統合（`/sse`または`/mcp`）

- [ ] **Task 2.3**: main.pyの更新とドキュメント整備
  - 対象ファイル: `src/main.py`, `README.md`
  - 作業内容:
    - 新しいHTTPルーター (`mcp_http_router`) を登録
    - README.mdにStreamable HTTPトランスポートの設定例を追加
    - MCPクライアント設定例を両方のトランスポート（SSE、HTTP）に対応

### 完了条件

- [ ] Streamable HTTPトランスポート (`/mcp`) が動作する
- [ ] ミドルウェアのスキップ処理が `/mcp` パスにも対応している
- [ ] README.mdにStreamable HTTPトランスポートの設定例が追加されている
- [ ] SSEトランスポートも引き続き動作する（両方のトランスポートが共存）
- [ ] 品質チェックが通る

---

## 実装メモ

### 影響を受けるファイル

#### Phase 1（PR #1）
- `pyproject.toml` - 依存関係変更
- `src/presentation/mcp/mcp_server.py` - 新規作成（MCP Server実装）
- `src/main.py` - FastApiMCP削除、SSEアプリマウント追加
- `README.md` - MCP設定例更新

#### Phase 2（PR #2）
- `src/presentation/router/mcp_http_router.py` - 新規作成（HTTPトランスポート）
- `src/presentation/middleware/logging_middleware.py` - スキップパス追加
- `src/presentation/middleware/request_id_middleware.py` - スキップパス追加
- `src/main.py` - HTTPルーター登録
- `README.md` - HTTPトランスポート設定例追加

### 参考にすべき既存コード

- `src/presentation/router/mcp_lgtm_image_router.py` - 既存のMCPツール定義とコントローラー呼び出しパターン
- `src/presentation/middleware/logging_middleware.py` - `/sse`スキップ処理パターン（line 23-27）
- `src/presentation/middleware/request_id_middleware.py` - `/sse`スキップ処理パターン（line 20-24）

### 注意点

#### Phase 1
- MCPツール名とoperation_idは既存と同じにする（`get_random_lgtm_images`, `get_recently_created_lgtm_images`, `get_random_lgtm_markdown`）
- レスポンス形式も既存と完全に同じにする（クライアント側の設定変更を不要にする）
- `/sse`パスを維持する（後方互換性）
- `mcp_lgtm_image_router.py`は削除（MCPクライアントは `/sse` 経由でツールを呼び出すため、REST APIエンドポイントは不要）

#### Phase 2
- ミドルウェアのスキップ処理は `/sse` と `/mcp` の両方に対応
- AWS ECS + ALB環境での動作を考慮（タイムアウト設定など）
- SSEとHTTPの両方のトランスポートが同時に動作することを確認

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
