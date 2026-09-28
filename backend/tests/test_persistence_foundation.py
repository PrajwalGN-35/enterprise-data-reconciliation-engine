from app.core.database import Base
from app.models import AuditLog, ReconciliationRun

def test_persistence_models_registered():
    assert AuditLog.__tablename__ == 'audit_logs'
    assert ReconciliationRun.__tablename__ == 'reconciliation_runs'
    assert 'audit_logs' in Base.metadata.tables
    assert 'reconciliation_runs' in Base.metadata.tables

def test_reconciliation_run_columns():
    expected = {
        'id', 'source_file_name', 'target_file_name', 'status',
        'source_record_count', 'target_record_count',
        'matched_record_count', 'discrepancy_record_count',
        'missing_target_record_count', 'review_required_record_count',
        'total_discrepancy_count', 'reconciliation_percentage',
        'exception_percentage', 'field_discrepancy_counts',
        'created_at', 'started_at', 'completed_at'
    }
    actual = {column.name for column in ReconciliationRun.__table__.columns}
    assert actual == expected
