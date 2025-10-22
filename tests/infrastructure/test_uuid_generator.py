# 絶対厳守：編集前に必ずAI実装ルールを読む

import uuid

from src.infrastructure.uuid_generator import UuidGenerator


def test_uuid_generator_generates_valid_uuid() -> None:
    """UuidGeneratorが有効なUUID文字列を生成することを確認."""
    # Arrange
    generator = UuidGenerator()

    # Act
    result = generator.generate()

    # Assert
    # UUID形式として解釈できることを確認
    parsed_uuid = uuid.UUID(result)
    assert str(parsed_uuid) == result


def test_uuid_generator_generates_unique_ids() -> None:
    """UuidGeneratorが異なるIDを生成することを確認."""
    # Arrange
    generator = UuidGenerator()

    # Act
    id1 = generator.generate()
    id2 = generator.generate()

    # Assert
    assert id1 != id2
