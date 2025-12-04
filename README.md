# lgtm-cat-api

LGTMeow用のFastAPIベースのWeb APIです。

## 技術スタック

### 言語・ランタイム
- **Python 3.13.9**

### Webフレームワーク
- **FastAPI 0.121.0+** - 高速なPython Webフレームワーク
- **Uvicorn 0.38.0+** - ASGIサーバー（開発サーバーとして使用）
  - **fastapi-mcp 0.4.0+** - MCP (Model Context Protocol) サーバー機能

### 認証
- **python-jose 3.5.0+** - JWT（JSON Web Token）の生成・検証
- **AWS Cognito** - ユーザー認証とアクセストークン管理

### エラー監視
- **Sentry** - アプリケーションエラーの検知・可視化・通知

### 開発ツール
- **uv** - 高速なPythonパッケージマネージャー
- **Ruff 0.14.3+** - 高速なPythonリンター・フォーマッター
- **mypy 1.18.2+** - 静的型チェッカー（strictモード）

## セットアップ

### 前提条件
- Python 3.13.9以上
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

##### 必須の環境変数

アプリケーションの起動に必須の環境変数です。未設定の場合は起動時にエラーが発生します。

```bash
# AWS Cognito設定（JWT認証）
export COGNITO_USER_POOL_ID=         # CognitoユーザープールID
export COGNITO_APP_CLIENT_ID=        # CognitoアプリクライアントID

# 画像取得設定（URL画像取得機能用）
export IMAGE_ALLOWED_DOMAIN=         # アクセス可能なドメイン（例: example.r2.cloudflarestorage.com）

# AWS S3 Vector設定（ベクトル検索機能用）
export S3_VECTOR_BUCKET_NAME=        # S3ベクトルストレージのバケット名
export S3_VECTOR_INDEX_NAME=         # S3ベクトルインデックス名

# データベース接続情報
export DATABASE_USER=                # データベースユーザー名
export DATABASE_PASSWORD=            # データベースパスワード
export DATABASE_HOST=                # データベースホスト
export DATABASE_NAME=                # データベース名
```

##### オプションの環境変数

デフォルト値が設定されているため、必要に応じて設定してください。

```bash
# LGTM画像のベースURL
export LGTM_IMAGES_BASE_URL=lgtm-images.lgtmeow.com  # デフォルト: lgtm-images.lgtmeow.com

# LGTM画像のアップロード先S3バケット
export UPLOAD_S3_BUCKET_NAME=        # デフォルト: 空文字

# ログ設定
export LOG_LEVEL=INFO                # デフォルト: INFO（DEBUG, INFO, WARNING, ERROR, CRITICAL）

# AWS Cognito設定
export COGNITO_REGION=ap-northeast-1 # デフォルト: ap-northeast-1

# AWS Bedrock設定（埋め込みモデル用）
export AWS_BEDROCK_REGION=us-east-1  # デフォルト: us-east-1
export AWS_BEDROCK_EMBEDDING_MODEL_ID=cohere.embed-v4:0  # デフォルト: cohere.embed-v4:0

# AWS S3 Vector設定
export S3_VECTOR_REGION=us-east-1    # デフォルト: us-east-1

# AWS Rekognition設定（画像認識機能用）
export AWS_REKOGNITION_REGION=ap-northeast-1  # デフォルト: ap-northeast-1

# Sentry設定（エラー監視）
export SENTRY_DSN=                   # デフォルト: 空文字（未設定時はSentry無効）
export SENTRY_ENVIRONMENT=development # デフォルト: development（例: development, staging, production）
```

##### テスト専用の環境変数

テスト実行時のみ必要な環境変数です。

```bash
# テスト用ローカルMySQL接続情報
export TEST_DATABASE_PASSWORD=       # テスト用DBユーザーパスワード
export TEST_DATABASE_ROOT_PASSWORD=  # テスト用DBルートパスワード（Docker Compose使用時）

# PlanetScale API設定（テスト用）
export PLANETSCALE_ORG_NAME=         # PlanetScale組織名
export PLANETSCALE_SERVICE_TOKEN_ID= # PlanetScaleサービストークンID
export PLANETSCALE_SERVICE_TOKEN=    # PlanetScaleサービストークン
export PLANETSCALE_DATABASE_NAME=    # PlanetScaleデータベース名
export PLANETSCALE_BRANCH_NAME=      # PlanetScaleブランチ名
```

**注意**: `.envrc` ファイルは `.gitignore` に含まれているため、リポジトリにコミットされません。

#### Sentryの設定

アプリケーションのエラー監視を有効にするには、以下の環境変数を設定します。

- **SENTRY_DSN**: SentryプロジェクトのDSN（Data Source Name）。この値が設定されていない場合、Sentryは無効化されます。
- **SENTRY_ENVIRONMENT**: 実行環境の識別子（例: `development`, `staging`, `production`）。Sentryダッシュボードでエラーをフィルタリングする際に使用されます。

サンプリングレートは環境に応じて自動設定されます：
- **prod**: トレース 20%、プロファイル 10%
- **その他の環境**: トレース 5%、プロファイル 1%

## 開発

### 開発サーバーの起動

```bash
make run
```

開発サーバーが http://0.0.0.0:8000 で起動します（自動リロード有効）。

または直接実行することもできます：

```bash
uv run python src/main.py
```

### コード品質チェック

```bash
# リンターでコードをチェック
make lint

# リンターで自動修正
make fix

# コードをフォーマット
make format

# 型チェック（strictモード、src/とtests/が対象）
make typecheck

# すべてのテストを実行
make test
```

すべてのコマンドは正しい仮想環境を使用するために`uv run`経由で実行されます（Makefileが自動的に対応）。

### コード品質要件

- **型チェック**: mypyを厳格モード（`--strict`）で`src/`と`tests/`ディレクトリに対して実行。すべての関数に戻り値の型を含む適切な型アノテーションが必要
- **リント・フォーマット**: Ruffを使用。CIはリントチェックとフォーマットチェックの両方を強制
- **CI**: すべてのPRは以下のジョブをパスする必要があります
  - ci (Ruffリントチェック)
  - format (Ruffフォーマットチェック)
  - typecheck (mypy厳格型チェック)
  - test (pytestによるテスト実行)

## API仕様

APIはシンプルなRESTパターンに従い、8つのエンドポイントを提供します。

### エンドポイント

#### 認証必須エンドポイント

1. **GET /lgtm-images** - ランダムなLGTM画像を返す
2. **POST /lgtm-images** - 新しいLGTM画像を作成（base64画像と拡張子を受け取る）
3. **GET /lgtm-images/recently-created** - 最近作成されたLGTM画像を返す
4. **POST /lgtm-images/search/text** - テキストからLGTM画像を検索
5. **POST /lgtm-images/search/image-from-data** - 画像データから類似したLGTM画像を検索
6. **POST /lgtm-images/search/image-from-url** - 署名付きURLから類似したLGTM画像を検索
7. **POST /cat-images/validate/url** - URLから画像を取得して猫画像判定
8. **POST /cat-images/validate/s3** - S3オブジェクト参照で猫画像判定

#### MCP専用エンドポイント（認証不要）

以下のエンドポイントはMCP専用として`/mcp`プレフィックス配下に公開されており、認証なしで利用できます：

1. **GET /mcp/lgtm-images** - ランダムなLGTM画像を返す
2. **GET /mcp/lgtm-images/recently-created** - 最近作成されたLGTM画像を返す

レスポンスモデルはPydanticのBaseModelを使用して定義されており、JSONフィールドにはキャメルケースを使用します（例: `imageUrl`, `imageExtension`）。

### 認証

通常のAPIエンドポイント（`/lgtm-images`、`/cat-images`など）はAWS Cognito JWTトークンによる認証が必要です。MCP専用の`/mcp/...`エンドポイントは認証不要で利用できます。

- **認証方式**: Bearer Token（JWT）
- **ヘッダー形式**: `Authorization: Bearer <access_token>`
- **トークン取得**: AWS Cognitoから発行されたアクセストークンを使用
- **エラーレスポンス**:
  - 401 Unauthorized - トークンが無効、期限切れ、または未提供の場合
- **認証不要**: `/mcp/lgtm-images`、`/mcp/lgtm-images/recently-created`

### MCP Server

本APIはMCP (Model Context Protocol) Serverとしても機能し、AIエージェントから直接利用できます。

#### MCP専用エンドポイント

以下のエンドポイントは`/mcp`プレフィックス配下に公開されており、**認証不要**で利用できます：

- **GET /mcp/lgtm-images** - ランダムなLGTM画像を取得
- **GET /mcp/lgtm-images/recently-created** - 最近作成されたLGTM画像を取得

#### Claudeからの利用方法

Claude Desktopの設定ファイル（`claude_desktop_config.json`）に以下を追加してください：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "lgtmeow": {
      "command": "/path/to/uvx",
      "args": [
        "mcp-proxy",
        "http://localhost:8000/sse"
      ]
    }
  }
}
```

※ [uv](https://docs.astral.sh/uv/)のインストールが必要です。

※ `command`には`uvx`のフルパスを指定してください。以下のコマンドで確認できます：

```bash
which uvx
```

設定後、Claudeを再起動し、`make run`でローカルサーバーを起動すると利用可能になります。

## プロジェクト構造

```
src/
├── domain/              # ドメイン層（ビジネスルールとエンティティ）
├── usecase/             # ユースケース層（アプリケーション固有のビジネスロジック）
├── infrastructure/      # インフラストラクチャ層（外部依存の実装）
├── presentation/        # プレゼンテーション層（HTTPリクエスト/レスポンス処理）
│   ├── router/         # FastAPI APIRouterを使ったルーティング定義
│   └── controller/     # HTTPリクエストを処理するコントローラー
├── log/                 # ロギング関連（横断的関心事）
├── sentry/              # Sentryエラー監視（横断的関心事）
└── main.py             # エントリーポイント
```

詳細なアーキテクチャ情報は `CLAUDE.md` および `src/CLAUDE.md` を参照してください。
