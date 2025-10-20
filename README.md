# lgtm-cat-api

LGTMeow用のFastAPIベースのWeb APIです。

## 技術スタック

### 言語・ランタイム
- **Python 3.12.4**

### Webフレームワーク
- **FastAPI 0.115.0+** - 高速なPython Webフレームワーク
- **Uvicorn 0.30.6+** - ASGIサーバー（開発サーバーとして使用）

### 開発ツール
- **uv** - 高速なPythonパッケージマネージャー
- **Ruff 0.6.8+** - 高速なPythonリンター・フォーマッター
- **mypy 1.11.2+** - 静的型チェッカー（strictモード）

## セットアップ

### 前提条件
- Python 3.12.4以上
- uv（インストール方法: https://docs.astral.sh/uv/getting-started/installation/）

### 依存関係のインストール

```bash
uv sync
```

クローン後や依存関係変更時に実行してください。すべての依存関係がインストール/同期されます。

### 環境変数の設定

プロジェクトは[direnv](https://direnv.net/)を使用して環境変数を管理します。

サンプルファイルをコピーして `.envrc` を作成します：

```bash
cp .envrc.example .envrc
```

必要に応じて `.envrc` ファイルを編集してください。

#### 環境変数一覧

```bash
# LGTM画像のベースURL
export LGTM_IMAGES_BASE_URL=

# PlanetScale接続情報
export DATABASE_USER=
export DATABASE_PASSWORD=
export DATABASE_HOST=
export DATABASE_NAME=
export SSL_CA_CERT=

# PlanetScale API設定（テスト用）
export PLANETSCALE_ORG_NAME=
export PLANETSCALE_SERVICE_TOKEN_ID=
export PLANETSCALE_SERVICE_TOKEN=
export PLANETSCALE_DATABASE_NAME=
export PLANETSCALE_BRANCH_NAME=

# テスト用ローカルMySQL接続情報
export TEST_DATABASE_PASSWORD=
export TEST_DATABASE_ROOT_PASSWORD=

# ログ設定
export LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

**注意**: `.envrc` ファイルは `.gitignore` に含まれているため、リポジトリにコミットされません。

## 開発

### 開発サーバーの起動

```bash
uv run python src/main.py
```

開発サーバーが http://0.0.0.0:8000 で起動します（自動リロード有効）。

### コード品質チェック

```bash
# リンターでコードをチェック
make lint

# リンターで自動修正
make fix

# コードをフォーマット
make format

# 型チェック（strictモード）
make typecheck

# すべてのテストを実行
make test
```

すべてのコマンドは正しい仮想環境を使用するために`uv run`経由で実行されます（Makefileが自動的に対応）。

### コード品質要件

- **型チェック**: mypyを厳格モード（`--strict`）で実行。すべての関数に戻り値の型を含む適切な型アノテーションが必要
- **リント・フォーマット**: Ruffを使用。CIはリントチェックとフォーマットチェックの両方を強制
- **CI**: すべてのPRは以下のジョブをパスする必要があります
  - ci (Ruffリントチェック)
  - format (Ruffフォーマットチェック)
  - typecheck (mypy厳格型チェック)
  - test (pytestによるテスト実行)

## API仕様

APIはシンプルなRESTパターンに従い、3つのエンドポイントを提供します。

### エンドポイント

1. **GET /lgtm-images** - ランダムなLGTM画像を返す
2. **POST /lgtm-images** - 新しいLGTM画像を作成（base64画像と拡張子を受け取る）
3. **GET /lgtm-images/recently-created** - 最近作成されたLGTM画像を返す

レスポンスモデルはPydanticのBaseModelを使用して定義されており、JSONフィールドにはキャメルケースを使用します（例: `imageUrl`, `imageExtension`）。

## プロジェクト構造

```
src/
├── domain/              # ドメイン層（ビジネスルールとエンティティ）
├── usecase/             # ユースケース層（アプリケーション固有のビジネスロジック）
├── infrastructure/      # インフラストラクチャ層（外部依存の実装）
├── presentation/        # プレゼンテーション層（HTTPリクエスト/レスポンス処理）
│   ├── router/         # FastAPI APIRouterを使ったルーティング定義
│   └── controller/     # HTTPリクエストを処理するコントローラー
└── main.py             # エントリーポイント
```

詳細なアーキテクチャ情報は `CLAUDE.md` および `src/CLAUDE.md` を参照してください。
