import json

from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.models import AuditLog, ReconciliationRun


def test_reconciliation_persistence_models_can_store_records():
    db_session = SessionLocal()

    try:
        run = ReconciliationRun(
            source_file_name="source.csv",
            target_file_name="target.csv",
            status="completed",
            started_at=datetime.now(timezone.utc),
            source_record_count=10,
            target_record_count=10,
            matched_record_count=8,
            discrepancy_record_count=2,
            missing_target_record_count=1,
            review_required_record_count=1,
            total_discrepancy_count=2,
            reconciliation_percentage=80.0,
            exception_percentage=20.0,
            field_discrepancy_counts={"amount": 2},
        )

        db_session.add(run)
        db_session.flush()

        audit = AuditLog(
            action="reconciliation_completed",
            entity_type="reconciliation_run",
            entity_id=run.id,
            details=json.dumps(
                {
                    "source_file_name": "source.csv",
                    "target_file_name": "target.csv",
                    "status": "completed",
                }
            ),
        )

        db_session.add(audit)
        db_session.commit()

        saved_run = db_session.get(
            ReconciliationRun,
            run.id,
        )

        assert saved_run is not None
        assert saved_run.status == "completed"
        assert saved_run.source_record_count == 10
        assert saved_run.matched_record_count == 8

        saved_audit = (
            db_session.query(AuditLog)
            .filter(AuditLog.entity_id == run.id)
            .first()
        )

        assert saved_audit is not None
        assert saved_audit.action == "reconciliation_completed"
        assert saved_audit.entity_type == "reconciliation_run"
        assert saved_audit.entity_id == run.id

    finally:
        db_session.close()

