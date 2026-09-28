import uuid

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.core.database import Base


class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    source_file_name = Column(String(255), nullable=False)
    target_file_name = Column(String(255), nullable=False)

    status = Column(
        String(50),
        nullable=False,
        default="completed",
    )

    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    source_record_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    target_record_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    matched_record_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    discrepancy_record_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    missing_target_record_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    review_required_record_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    total_discrepancy_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    reconciliation_percentage = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    exception_percentage = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    field_discrepancy_counts = Column(
        JSONB,
        nullable=False,
        default=dict,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
