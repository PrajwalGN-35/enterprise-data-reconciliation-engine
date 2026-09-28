from app.core.database import Base, engine
from app.models import AuditLog, ReconciliationRun


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
