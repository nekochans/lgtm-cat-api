# 実行計画: Issue #88 - MCPツール `get_random_lgtm_markdown` を追加する

## Issue情報

- **Issue URL**: https://github.com/nekochans/lgtm-cat-api/issues/88
- **作成日**: 2025-12-08

## 概要

ランダムなLGTM画像をマークダウン形式で返すMCPツール `get_random_lgtm_markdown` を追加する。AIエージェントがコードレビューやPR承認コメントで直接利用できるよう、マークダウン形式のレスポンスを提供する。

## 完了の定義（Issueより）

- [x] MCPツール `get_random_lgtm_markdown` が追加されている
- [x] ツールを呼び出すとランダムな1件のLGTM画像がマークダウン形式で返される
- [x] レスポンス形式は `[![LGTMeow](画像URL)](https://lgtmeow.com)` の形式である
- [x] 画像が取得できない場合は適切なエラーが返される

---

## 完了要件

### テスト要件

- [x] ユースケースのテストが追加されている
  - [x] 正常系: マークダウン形式の文字列が返される
  - [x] 異常系: 画像が0件の場合に例外が発生する
- [x] コントローラーのテストが追加されている
  - [x] 正常系: マークダウン形式でレスポンスが返される
  - [x] 異常系: 画像が0件の場合に404エラーを返す

### ドキュメント要件

- [x] OpenAPI仕様が自動生成される（コード内のdocstringで対応）

### 品質要件（固定）

- [x] `make lint` が通る
- [x] `make typecheck` が通る
- [x] `make test` が通る

---

## フェーズ構成

| フェーズ | 説明 | タスク数 |
|---------|------|---------|
| Phase 1 | ユースケース層の実装 | 2 |
| Phase 2 | コントローラー層の実装 | 2 |
| Phase 3 | プレゼンテーション層の実装 | 1 |

---

## Phase 1: ユースケース層の実装

### 目的

マークダウン形式でランダムLGTM画像を取得するユースケースを実装する。

### タスク一覧

- [x] **Task 1.1**: ユースケースの追加
  - 対象ファイル: `src/usecase/extract_random_lgtm_markdown_usecase.py`（新規作成）
  - 作業内容:
    - `ExtractRandomLgtmMarkdownUsecase` クラスを作成
    - `execute(repository, base_url)` 静的メソッドを実装
    - リポジトリから直接1件取得（`repository.fetch_random_lgtm_images(limit=1)`）
    - 取得件数が0件の場合は `ErrRecordCount` を発生させる
    - 取得した画像URLを `[![LGTMeow]({url})](https://lgtmeow.com)` 形式に変換して返す
    - 戻り値の型は `str`（マークダウン文字列）

- [ ] **Task 1.2**: ユースケーステストの追加
  - 対象ファイル: `tests/usecase/test_extract_random_lgtm_markdown_usecase.py`（新規作成）
  - 作業内容:
    - 実DB（`test_db_session`）を使用してテスト
    - 正常系テスト: 返り値がマークダウン形式の文字列であることを検証
    - 正常系テスト: `[![LGTMeow]({url})](https://lgtmeow.com)` 形式であることを検証
    - 異常系テスト: 画像が0件の場合に `ErrRecordCount` が発生することを検証

### 完了条件

- [ ] ユースケースがマークダウン形式の文字列を返す
- [ ] テストがすべてパスする
- [ ] 品質チェックが通る

---

## Phase 2: コントローラー層の実装

### 目的

ユースケースを呼び出し、レスポンスを返すコントローラーメソッドを実装する。

### 依存関係

- Phase 1 の完了が必要

### タスク一覧

- [x] **Task 2.1**: コントローラーメソッドの追加
  - 対象ファイル: `src/presentation/controller/lgtm_image_controller.py`
  - 作業内容:
    - `exec_random_markdown(repository, base_url, lgtmeow_url)` メソッドを追加
    - `ExtractRandomLgtmMarkdownUsecase.execute(repository, base_url, lgtmeow_url)` を呼び出す
    - 結果を `LgtmImageMarkdownResponse` モデルで `JSONResponse` として返す（`status_code=200`）
    - `ErrRecordCount` 例外をキャッチして 404 エラーを返す
    - その他の例外は `create_error_response` で 500 エラーを返す

- [x] **Task 2.2**: コントローラーテストの追加
  - 対象ファイル: `tests/presentation/controller/test_lgtm_image_controller_exec.py`
  - 作業内容:
    - `TestLgtmImageControllerExecRandomMarkdown` クラスを追加
    - 実DB（`test_db_session`）を使用してテスト
    - 正常系テスト: レスポンスが `JSONResponse` であることを検証
    - 異常系テスト: 画像が0件の場合に404エラーを返すことを検証

### 完了条件

- [x] コントローラーメソッドがユースケースを呼び出してレスポンスを返す
- [x] テストがすべてパスする
- [x] 品質チェックが通る

---

## Phase 3: プレゼンテーション層の実装

### 目的

MCPルーターに新しいエンドポイントを追加し、MCPツールとして公開する。

### 依存関係

- Phase 2 の完了が必要

### タスク一覧

- [x] **Task 3.1**: MCPルーターにエンドポイントを追加
  - 対象ファイル: `src/presentation/router/mcp_lgtm_image_router.py`
  - 作業内容:
    - `@router.get("/lgtm-images/markdown")` エンドポイントを追加
    - `operation_id="get_random_lgtm_markdown"` を設定
    - `response_model=LgtmImageMarkdownResponse` を設定
    - `summary="Get a random LGTM image in markdown format"` を設定
    - `description`: AIエージェント向けの詳細説明を追加
    - `response_description="Markdown formatted LGTM image"` を設定
    - `tags=["mcp_tool"]` を設定（MCP公開用）
    - `responses` で 200, 404, 500 の例を定義
      - 200: `{"markdown": "[![LGTMeow](https://lgtm-images.lgtmeow.com/2022/03/23/10/9738095a-f426-48e4-be8d-93f933c42917.webp)](https://lgtmeow.com)"}`
      - 404: `{"error": "Insufficient LGTM images available"}`
      - 500: `{"error": "Internal server error"}`
    - `LgtmImageController.exec_random_markdown(repository, base_url, lgtmeow_url)` を呼び出す

### 完了条件

- [x] MCPツールとしてエンドポイントが公開される
- [x] OpenAPIドキュメントに仕様が反映される
- [x] 品質チェックが通る

---

## 実装メモ

### 影響を受けるファイル

- `src/usecase/extract_random_lgtm_markdown_usecase.py` - 新規作成
- `src/presentation/controller/lgtm_image_controller.py` - 新メソッド追加
- `src/presentation/controller/lgtm_image_response.py` - `LgtmImageMarkdownResponse` モデル追加
- `src/presentation/router/mcp_lgtm_image_router.py` - 新エンドポイント追加
- `tests/usecase/test_extract_random_lgtm_markdown_usecase.py` - 新規作成
- `tests/presentation/controller/test_lgtm_image_controller_exec.py` - テスト追加

### 参考にすべき既存コード

- `src/usecase/extract_random_lgtm_images_usecase.py` - ユースケースのパターン
- `src/presentation/controller/lgtm_image_controller.py` の `exec()` メソッド - コントローラーパターン
- `src/presentation/router/mcp_lgtm_image_router.py` の既存エンドポイント - ルーター定義パターン
- `tests/usecase/test_extract_random_lgtm_images_usecase.py` - ユースケーステストパターン
- `tests/presentation/controller/test_lgtm_image_controller_exec.py` の既存テスト - コントローラーテストパターン

### 注意点

- **責務の分離**
  - マークダウン変換ロジックはユースケース層に配置
  - コントローラーはユースケースを呼び出してレスポンスを返すだけ

- **レスポンス形式はJSON（`application/json`）**
  - MCP公開の手段としてFastAPI MCPを使用しており、他のエンドポイントはすべてJSON形式でレスポンスを返している
  - `get_random_lgtm_markdown` だけが `PlainTextResponse` を返すと統一感が失われるため、JSON形式に変更
  - `LgtmImageMarkdownResponse` モデルを使用し、`create_json_response` で返す
  - レスポンス形式: `{"markdown": "[![LGTMeow](画像URL)](https://lgtmeow.com)"}`

- **取得件数は1件のみ**
  - ユースケース内でリポジトリから直接1件取得（`repository.fetch_random_lgtm_images(limit=1)`）
  - 他のユースケースは呼び出さない（ユースケース間の依存を避ける）

- **マークダウン形式**
  - `[![LGTMeow](画像URL)](https://lgtmeow.com)` の形式に厳密に従う
  - 画像のalt textは "LGTMeow" 固定
  - リンク先は "https://lgtmeow.com" 固定

- **エラーハンドリング**
  - ユースケース層: `ErrRecordCount` をそのまま伝播
  - コントローラー層: `ErrRecordCount` をキャッチして 404、その他は 500

- **型アノテーション**
  - すべての関数に適切な型アノテーションを付ける
  - `mypy --strict` を通過する必要がある

