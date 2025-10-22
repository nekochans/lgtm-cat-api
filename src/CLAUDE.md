# ディレクトリ構成

## srcディレクトリ説明

### domain（ドメイン層）

**責務**: ビジネスルールとエンティティの定義

- ドメインエンティティ（LgtmImageなど）
- リポジトリインターフェース（抽象定義のみ）
- 純粋なビジネスロジック

### usecase（ユースケース層）

**責務**: アプリケーション固有のビジネスロジック

- ユースケースの実装
- ドメインエンティティを組み合わせた処理フロー
- リポジトリインターフェースを使用（実装には依存しない）

### infrastructure（インフラストラクチャ層）

**責務**: 外部依存の具体的な実装

- データベース接続設定
- リポジトリの実装（domain層のインターフェースを実装）
- 外部サービス連携（S3、認証など）
- DBモデル ↔ ドメインエンティティの変換

### presentation（プレゼンテーション層）

**責務**: HTTPリクエスト/レスポンスの処理

- **router/** - FastAPI APIRouterを使ったルーティング定義
  - エンドポイント定義とOpenAPIドキュメント設定
  - 依存性注入（DI）の設定（リポジトリインスタンス生成など）
  - FastAPIの`Depends`を使った設定値の注入
- **controller/** - HTTPリクエストを処理するコントローラークラス
  - ユースケースの呼び出し
  - レスポンス形式への変換（ドメイン → レスポンスモデル）
  - エラーハンドリングとHTTPステータスコード制御


### main.py（エントリーポイント）

**責務**: アプリケーションの起動とルーター登録

- FastAPIアプリケーション定義
- APIRouterの登録（`app.include_router()`）
- サーバー起動設定

**重要な設計方針**:
- `main.py`は極力シンプルに保つ
- 個別のルーティング定義は各ルーターファイルで行う

## tests（テスト層）

**責務**: 各層のテストコード

テストディレクトリは`src`と同階層の`tests/`ディレクトリに配置します。

詳細なテスト方針については @tests/CLAUDE.md を参照してください。

## 依存関係

- **domain層**: 他のどの層にも依存しない（純粋なビジネスロジック）
- **usecase層**: domain層のみに依存
- **infrastructure層**: domain層のみに依存（インターフェースを実装）
- **presentation層**: usecase層、domain層、infrastructure層に依存

## 重要な設計方針

### 型定義のパターン

#### ドメインエンティティ（domain層）
- **TypedDict**を使用してビジネスエンティティを定義
- 例: `LgtmImage(TypedDict)` - 辞書アクセスで柔軟な操作が可能
- ドメインの純粋性を保つために軽量な型定義を採用
- **Required/NotRequired型ヒント**を使用してフィールドの必須性を明示
  - すべてのフィールドに`Required[型]`または`NotRequired[型]`を明記
  - 例: `id: Required[str]`, `optional_field: NotRequired[str]`
  - 型の意図を明確にし、型安全性を向上

#### レスポンスモデル（presentation層）
- **Pydantic BaseModel**を使用してAPI応答モデルを定義
- `Field(alias="...")` でキャメルケース化（Python側はスネークケース）
- OpenAPI仕様の自動生成に対応
- 例: `LgtmImageItem(BaseModel)`, `LgtmImageRandomListResponse(BaseModel)`

### エラーハンドリング

#### ビジネスエラー（domain層）
- カスタム例外クラスを定義（例: `ErrRecordCount`）
- ビジネスルール違反を明示的に表現

#### HTTPエラー変換（controller層）
- ドメインの例外をキャッチしてHTTPステータスコードに変換
- 例: `ErrRecordCount` → 404 Not Found
- すべての予期しない例外は500 Internal Server Errorに変換

### 依存性注入（DI）パターン

#### リポジトリ注入
- router層でリポジトリインスタンスを生成
- controllerにインターフェース型として渡す
- インターフェースを通じた疎結合を実現

#### 設定値の注入
- FastAPIの`Depends`を使用して設定値を注入
- 例: `base_url: str = Depends(get_lgtm_images_base_url)`
- 環境変数管理を`config.py`に集約

### Controller レスポンス設計ルール

#### JSONResponse返却の統一ルール

**Controller から `JSONResponse` を返す際は、`src/presentation/controller/response_helper.py`の`create_json_response`関数を必ず使用してください**

この関数により、クライアントに不要なフィールドを返さず、クリーンなAPIレスポンスを保つことができます。

#### 実装例：

```python
from src.presentation.controller.response_helper import create_json_response
from src.presentation.controller.lgtm_image_response import LgtmImageRandomListResponse

# レスポンスモデルを作成
response = LgtmImageRandomListResponse(lgtmImages=image_items)

# create_json_response関数でJSONResponseを生成
return create_json_response(response)

# ステータスコードを指定する場合
return create_json_response(response, status_code=201)
```

#### パラメータの説明：

- **`exclude_none=True`**: 値が `None` のフィールドをJSONから除外します
- **`exclude_unset=True`**: Pydanticモデルのインスタンス化時に明示的に設定されなかったフィールドをJSONから除外します

#### 注意事項：

- 空文字 `""` は **どちらのパラメータでも除外されません**
- デフォルト値を持つフィールドで、そのデフォルト値をクライアントに返したい場合は、明示的に設定する必要があります
- **エラーレスポンス（辞書形式）**の場合は、従来通り`JSONResponse`を直接使用してください（例: `JSONResponse(status_code=404, content={"error": "..."})`）
