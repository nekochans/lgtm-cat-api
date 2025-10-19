# テストガイド

## テストディレクトリ構成

テストディレクトリは`src`と同階層の`tests/`ディレクトリに配置し、`src`ディレクトリの構造を反映します。

```
tests/
├── domain/          # ドメイン層のテスト
├── usecase/         # ユースケース層のテスト
├── infrastructure/  # インフラストラクチャ層のテスト
├── presentation/    # プレゼンテーション層のテスト
└── e2e/             # E2Eテスト
```

## テストコードの必須事項

### ソースファイル先頭コメント

全てのテストファイル（`test_*.py`）の先頭に必ず以下のコメントを記載してください。

```python
# 絶対厳守：編集前に必ずAI実装ルールを読む
```

### テストフレームワーク

- **pytest** - メインのテストフレームワーク

## テスト実行コマンド

```bash
# すべてのテストを実行
pytest

# 特定のディレクトリのみ実行
pytest tests/domain/
pytest tests/usecase/
pytest tests/e2e/

# カバレッジレポート付き実行
pytest --cov=src --cov-report=html
```

## テストコードの品質要件

### 型チェック

- テストコードも型アノテーションを付ける
- `mypy --strict`を通過する必要がある

### コードスタイル

- Ruffのリントとフォーマットに準拠
- `make lint`と`make format`を通過する必要がある

## データベーステスト

### test_db_session フィクスチャの使用

データベーステストには、`conftest.py` で定義された `test_db_session` フィクスチャを使用します。

このフィクスチャは：
- テスト実行ごとにランダムな名前のデータベースを作成
- PlanetScaleのスキーマからテーブルを自動作成
- テスト完了後にデータベースを自動削除

```python
@pytest.mark.asyncio
async def test_find_all_ids(test_db_session: AsyncSession) -> None:
    # test_db_sessionを使用してテスト
    repository = LgtmImageRepository(test_db_session)
```

### ランダム性の制御

ランダム要素を含むテストでは、`random.seed()` でシードを固定して再現性を確保します。

```python
import random

random.seed(42)  # ランダム性を固定
result = await ExtractRandomLgtmImagesUsecase.execute(...)
```

## テストデータのセットアップ

テストデータの挿入には、`tests/fixtures/test_data_helpers.py` で定義されたヘルパー関数を使用します。

```python
from tests.fixtures.test_data_helpers import insert_test_lgtm_images

# テストデータを10件挿入
await insert_test_lgtm_images(test_db_session, count=10)
```

## テストヘルパー関数

### 配置場所

テストヘルパー関数は `tests/fixtures/` ディレクトリに配置します。

- **test_data_helpers.py** - テストデータ作成ヘルパー
- **test_database.py** - データベース関連ヘルパー

### ヘルパー関数の実装パターン

```python
async def insert_test_lgtm_images(
    session: AsyncSession, count: int = 2
) -> list[LgtmImageModel]:
    """テスト用のLGTM画像データを挿入する.

    Args:
        session: データベースセッション
        count: 挿入するデータ件数

    Returns:
        挿入されたLgtmImageModelのリスト
    """
    now = datetime.now()
    images = []
    for i in range(1, count + 1):
        image = LgtmImageModel(
            filename=f"test{i}.webp",
            path=f"/images/test{i}.webp",
            created_at=now,
            updated_at=now,
        )
        session.add(image)
        images.append(image)

    await session.commit()

    # IDを取得するためにリフレッシュ
    for image in images:
        await session.refresh(image)

    return images
```
