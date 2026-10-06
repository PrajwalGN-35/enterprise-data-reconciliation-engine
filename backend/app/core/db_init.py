from app.core.database import Base, engine
from ..models import AuditLog, ReconciliationRun, QualityRun


def init_db() -> None:
    from ..models.quality_assessment import QualityAssessment

Base.metadata.create_all(bind=engine)
from ..models.quality_run import QualityRun

