from typing import Any

from pydantic import BaseModel


class ReconciliationRunHistoryItem(BaseModel):
    run_id: str
    source_file_name: str
    target_file_name: str
    status: str
    started_at: str
    completed_at: str | None
    source_record_count: int
    target_record_count: int
    matched_record_count: int
    discrepancy_record_count: int
    missing_target_record_count: int
    review_required_record_count: int
    total_discrepancy_count: int
    reconciliation_percentage: float
    exception_percentage: float


class ReconciliationRunHistoryResponse(BaseModel):
    total: int
    limit: int
    offset: int
    runs: list[ReconciliationRunHistoryItem]


class ReconciliationRunDetailResponse(BaseModel):
    run_id: str
    source_file_name: str
    target_file_name: str
    status: str
    started_at: str
    completed_at: str | None
    source_record_count: int
    target_record_count: int
    matched_record_count: int
    discrepancy_record_count: int
    missing_target_record_count: int
    review_required_record_count: int
    total_discrepancy_count: int
    reconciliation_percentage: float
    exception_percentage: float
    field_discrepancy_counts: dict[str, Any]


class AuditLogResponse(BaseModel):
    id: str
    action: str
    entity_type: str | None
    entity_id: str | None
    details: str | None
    created_at: str


class ReconciliationAuditResponse(BaseModel):
    run_id: str
    audit_logs: list[AuditLogResponse]
