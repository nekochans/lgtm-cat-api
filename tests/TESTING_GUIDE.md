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
