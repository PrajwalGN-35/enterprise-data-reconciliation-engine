from app.core.database import Base, engine
from ..models import AuditLog, ReconciliationRun


def init_db() -> None:
    from ..models.quality_assessment import QualityAssessment

Base.metadata.create_all(bind=engine)
