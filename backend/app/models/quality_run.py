from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class QualityRun(Base):
    __tablename__ = "quality_runs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    dataset: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    column_count: Mapped[int] = mapped_column(Integer, nullable=False)
    rule_count: Mapped[int] = mapped_column(Integer, nullable=False)
    failed_rule_count: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    risk: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    issues_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="[]",
    )
    rule_scores_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="[]",
    )
