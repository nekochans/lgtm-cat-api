# 🚨🚨🚨 【重要】ソースファイル必須事項（絶対厳守）

絶対厳守：編集前に必ずルールを読む

本ドキュメントはコーディング用AIエージェント向けの資料です。

## ソースファイル先頭コメント必須

全てのソースファイル（.py）の先頭に必ず以下のコメントを記載してください。

```python
# 絶対厳守：編集前に必ずAI実装ルールを読む
```

既存ファイルにコメントがない場合は必ず追加してください。

## 他のファイルへの参照

**以下のように @<path> の形式で書かれている場合は別のファイルへの参照になりますので、対象ファイルを探して内容を確認してください。**

**以下に記載例を示します。**

@src/main.py（src/main.py を参照）
@.github/PULL_REQUEST_TEMPLATE.md （.github/PULL_REQUEST_TEMPLATE.md を参照）

## プロジェクト概要

LGTMeow用のFastAPIベースのWeb APIです。依存関係管理には`uv`を使用し、厳格な型チェックを有効にしたPythonで記述されています。

## 技術スタック

### 言語・ランタイム
- **Python 3.12.4** - メインプログラミング言語

### Webフレームワーク
- **FastAPI 0.115.0+** - 高速なPython Webフレームワーク
- **Uvicorn 0.30.6+** - ASGIサーバー（開発サーバーとして使用）

### 開発ツール
- **uv** - 高速なPythonパッケージマネージャー
- **Ruff 0.6.8+** - 高速なPythonリンター・フォーマッター
- **mypy 1.11.2+** - 静的型チェッカー（strictモード）

## 開発コマンド

### パッケージ管理
- `uv sync` - すべての依存関係をインストール/同期（クローン後や依存関係変更時に実行）

### 開発サーバー
- `python src/main.py` - 開発サーバーを http://0.0.0.0:8000 で起動（自動リロード有効）
- または: `uv run python src/main.py`

### コード品質チェック
- `make lint` - Ruffリンターでコードをチェック
- `make fix` - Ruffリンターで自動修正
- `make format` - Ruffでコードをフォーマット
- `make typecheck` - mypyで`src/`ディレクトリを厳格モードで型チェック
- `make test` - pytestですべてのテストを実行

すべてのコマンドは正しい仮想環境を使用するために`uv run`経由で実行する必要があります。Makefileは既にこれに対応しています。

## アーキテクチャ

### プロジェクト構造
@src/CLAUDE.md を参照してください。

### API設計
APIはシンプルなRESTパターンに従い、3つのエンドポイントがあります：

1. **GET /lgtm-images** - ランダムなLGTM画像を返す
2. **POST /lgtm-images** - 新しいLGTM画像を作成（base64画像と拡張子を受け取る）
3. **GET /lgtm-images/recently-created** - 最近作成されたLGTM画像を返す

レスポンスモデルはPydanticのBaseModelを使用して定義されています。

### レスポンスモデルのパターン
- 各エンドポイントは専用のレスポンスモデルを持ちます（例: `LgtmImageRandomListResponse`, `LgtmImageRecentlyCreatedListResponse`）
- POSTエンドポイント用のリクエストモデルが定義されています（例: `LgtmImageCreateRequest`）
- モデルはJSONフィールドにキャメルケースを使用します（例: `imageUrl`, `imageExtension`）

## コード品質要件

### 型チェック
- mypyは厳格モード（`--strict`）で実行されます
- すべての関数は戻り値の型を含む適切な型アノテーションが必要です

### リントとフォーマット
- リントとフォーマットの両方にRuffを使用します
- CIはリントチェックとフォーマットチェックの両方を強制します
- `make fix`で自動修正し、その後`make format`でフォーマットします

### CIパイプライン
CIは4つの独立したジョブを実行します：
1. **ci** - Ruffリントチェック
2. **format** - Ruffフォーマットチェック
3. **typecheck** - mypy厳格型チェック
4. **test** - pytestによるテスト実行

PRをマージするにはすべてのジョブがパスする必要があります。

## GitとGitHubワークフロールール

### GitHubの利用ルール

GitHubのMCPサーバーを利用してGitHubへのPRを作成する事が可能です。

許可されている操作は以下の通りです。

- GitHubへのPRの作成
- GitHubへのPRへのコメントの追加
- GitHub Issueへのコメントの追加

### PR作成ルール

- ブランチはユーザーが作成しますので現在のブランチをそのまま利用します
- PRのタイトルは日本語で入力します
- PRの作成先は特別な指示がない場合は `main` ブランチになります
- PRの説明欄は @.github/PULL_REQUEST_TEMPLATE.md を参考に入力します
- 対応issueがある場合は、PRの説明欄に `#<issue番号>` を記載します
- Issue番号は現在のブランチ名から取得出来ます、例えば `feature/issue7/add-docs` の場合は `7` がIssue番号になります
- PRの説明欄には主に以下の情報を含めてください

#### PRの説明欄に含めるべき情報

- 変更内容の詳細説明よりも、なぜその変更が必要なのかを重視
- 他に影響を受ける機能やAPIエンドポイントがあれば明記

#### 以下の情報はPRの説明欄に記載する事を禁止する

- 1つのissueで1つのPRとは限らないので `fix #issue番号` や `close #issue番号` のようなコメントは禁止します
- 全てのテストをパス、Linter、型チェックを通過などのコメント（テストやCIが通過しているのは当たり前でわざわざ書くべき事ではない）

## コーディング時に利用可能なツール

コーディングを効率的に行う為のツールです。必ず以下に目を通してください。

### Serena MCP ― コード検索・編集ツールセット（必ず優先）

| 分類                        | 主要ツール (mcp**serena**)                                                                        | 典型的な用途                                     |
| --------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| **ファイル / ディレクトリ** | `list_dir` / `find_file`                                                                          | ツリー俯瞰・ファイル名で高速検索                 |
| **全文検索**                | `search_for_pattern` / `replace_regex`                                                            | 正規表現を含む横断検索・一括置換                 |
| **シンボル検索**            | `get_symbols_overview` / `find_symbol` / `find_referencing_symbols`                               | 定義探索・参照逆引き                             |
| **シンボル編集**            | `insert_after_symbol` / `insert_before_symbol` / `replace_symbol_body`                            | 挿入・追記・リファクタ                           |
| **メモリ管理**              | `write_memory` / `read_memory` / `list_memories` / `delete_memory`                                | `.serena/memories/` への長期知識 CRUD            |
| **メンテナンス**            | `restart_language_server` / `switch_modes` / `summarize_changes` / `prepare_for_new_conversation` | LSP 再起動・モード切替・変更要約・新チャット準備 |

> **禁止**: 組み込み `Search / Read / Edit / Write` ツールは使用しない。
> **ロード手順**: チャット開始直後に `/mcp__serena__initial_instructions` を必ず実行してから作業を行う。

Serena MCPが使えない環境では仕方ないので通常の `Search / Read / Edit / Write` を使用しても良いが、Serena MCPの機能を優先的に利用すること。
### Gemini CLI ― Web 検索専用

外部情報を取得する必要がある場合は、次の Bash ツール呼び出しを **唯一の手段として使用** する。

```bash
gemini --prompt "WebSearch: <query>"
```

`gemini` が使えない環境の場合は通常のWeb検索ツールを使っても良い。

## **絶対禁止事項**

1. **依頼内容に関係のない無駄な修正を行う行為は絶体に禁止。**
2. **ビジネスロジックが誤っている状態で、テストコードを“上書きしてまで”合格させる行為は絶対に禁止。**
