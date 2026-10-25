import uuid

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.sql import func

from ..core.database import Base


class CrossSystemReport(Base):
    __tablename__ = "cross_system_reports"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    schema_version = Column(String(32), nullable=False)
    source_system = Column(String(255), nullable=False)
    source_dataset = Column(String(255), nullable=False)
    target_system = Column(String(255), nullable=False)
    target_dataset = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False, default="persisted")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    payload = Column(Text, nullable=False)
