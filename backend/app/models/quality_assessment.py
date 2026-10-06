from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class QualityAssessment(Base):
    __tablename__ = "quality_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(
        String,
        ForeignKey("reconciliation_runs.id"),
        nullable=False,
        index=True,
    )

    dataset = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    risk = Column(String, nullable=False)
    rule_count = Column(Integer, nullable=False, default=0)
    failed_rule_count = Column(Integer, nullable=False, default=0)
    rule_scores = Column(Text, nullable=False, default="[]")

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    reconciliation_run = relationship(
        "ReconciliationRun",
        back_populates="quality_assessments",
    )
