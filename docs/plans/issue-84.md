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

- [x] MCP専用ルーターのテストは**作成しない**（理由は後述）
- [x] 既存エンドポイントが従来通り動作すること（回帰テストは既存テストで担保済み）

#### MCP専用ルーターのテストを作成しない理由

1. **Controllerテストで十分カバーされている**
   - `tests/presentation/controller/test_lgtm_image_controller_exec.py`でビジネスロジック・レスポンス形式は既にテスト済み
   - MCPルーターは同じControllerを呼び出すだけなので、重複テストとなる

2. **認証なしの確認はルーター定義で明らか**
   - MCPルーターの`dependencies=[]`により認証が不要であることは自明
   - コードレビューで確認可能な範囲

3. **依存性注入の動作はFastAPIフレームワークの責任**
   - FastAPIの`Depends`が正しく動作するかはフレームワーク側のテストで担保
   - アプリケーション側でテストする必要性が低い

4. **CI環境での実行に課題がある**
   - Routerテストは実DB接続が必要
   - 遅延インポートでテスト収集時のエラーは回避できるが、フィクスチャ実行時に環境変数未設定エラーが発生する
   - CIでDB環境変数を設定するか、テストをスキップする対応が必要となり、得られる価値に対してコストが高い

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

- [x] **Task 1.4**: テスト方針の決定
  - **結論**: MCP専用ルーターのテストは作成しない
  - **理由**: 上記「MCP専用ルーターのテストを作成しない理由」を参照

### 完了条件

- [x] MCPクライアントから認証なしで画像取得できる
- [x] 既存の認証付きエンドポイントは従来通り動作する
- [x] 既存テストがすべてパスする
- [x] 品質チェックが通る

---

## 実装メモ

### 影響を受けるファイル

- `pyproject.toml` - `fastapi-mcp`依存を追加
- `src/presentation/router/mcp_lgtm_image_router.py` - MCP専用ルーター（新規作成）
- `src/main.py` - FastAPIMCP統合とルーター登録

### 参考にすべき既存コード

- `src/presentation/router/lgtm_image_router.py` - 既存のLGTM画像ルーター（ルーターパターン）
- `src/presentation/controller/lgtm_image_controller.py` - 再利用するコントローラー

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

### MCPツール名の命名規則

MCPツールの`operation_id`は以下のように命名した：

| operation_id | 説明 |
|--------------|------|
| `get_random_lgtm_images` | ランダムなLGTM画像を取得 |
| `get_recently_created_lgtm_images` | 最近作成されたLGTM画像を取得 |

**`get_`プレフィックスを採用した理由:**

1. **MCPサーバーの標準的な命名慣例に準拠**
   - Anthropic公式のGitHub MCPサーバーでは`get_issue`, `get_commit`, `get_file_contents`など`get_`プレフィックスが標準的に使用されている
   - 他の主要MCPサーバー（Serena, Context7等）も同様に`get_`を採用

2. **CRUDパターンとの親和性**
   - `get`/`list`/`create`/`update`/`delete`の標準動詞パターンに沿っている
   - 読み取り専用操作に対して`get`は直感的

3. **HTTPメソッドとの整合性**
   - これらは`GET`リクエストのエンドポイントであり、`get_`プレフィックスはHTTPセマンティクスと一致

**検討した代替案:**
- `fetch_random_lgtm_images` - 外部APIからの取得を強調するが、MCPの慣例から外れる
- `list_random_lgtm_images` - コレクションを返すことを強調するが、「ランダム」という性質を考慮すると`get`の方が適切

### NGINX SSEエンドポイント用設定

MCP ServerはSSE（Server-Sent Events）でクライアントと通信するため、NGINXで専用の設定が必要。

#### 必須設定

| 設定項目 | 値 | 理由 |
|---------|-----|------|
| `proxy_buffering` | off | レスポンスを即座にクライアントへ転送（SSEの即時性確保） |
| `proxy_cache` | off | キャッシュによる遅延を防止 |
| `chunked_transfer_encoding` | on | ストリーミング転送を有効化 |
| `proxy_set_header Connection` | "" | HTTP/1.1のKeep-Alive接続を維持 |

#### タイムアウト設定について

タイムアウト設定（`proxy_connect_timeout`, `proxy_send_timeout`, `proxy_read_timeout`）はすべて**デフォルト値（60秒）のまま**で問題ない。

**理由:**
- このAPIで提供するMCPツールはDB検索のみで、1秒未満で完了する
- SSEではデータ受信のたびにタイムアウトタイマーがリセットされるため、アクティブな接続は切れない
- idle状態で60秒経過して接続が切れても、MCPクライアント（Claude Desktop等）は自動的に再接続する
- ALBのidle_timeout（60秒）もデフォルトのままで変更不要
