# 絶対厳守：編集前に必ずAI実装ルールを読む

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class LgtmImageModel(Base):
    __tablename__ = "lgtm_images"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, nullable=False
    )
    filename: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=False
    )
    path: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
