from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class QualityIssueResponse(BaseModel):
    rule: str
    severity: str
    message: str
    column: str | None = None
    row_indices: list[int] = Field(default_factory=list)
    affected_rows: int = 0
    impact: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class QualityRuleResultResponse(BaseModel):
    rule: str
    passed: bool
    issue_count: int
    affected_rows: int
    issues: list[QualityIssueResponse] = Field(default_factory=list)


class QualityRunResponse(BaseModel):
    run_id: str | None = None
    dataset: str
    row_count: int
    column_count: int
    rule_count: int
    failed_rule_count: int
    score: float
    risk: str
    created_at: datetime | None = None
    rule_scores: list[dict[str, Any]] = Field(default_factory=list)
    issues: list[QualityIssueResponse] = Field(default_factory=list)


class QualityProfileRequest(BaseModel):
    dataset: str = Field(min_length=1)
    data: list[dict[str, Any]]
    matching_fields: list[str] = Field(default_factory=list)


class QualityValidateRequest(BaseModel):
    dataset: str = Field(min_length=1)
    data: list[dict[str, Any]]
    matching_fields: list[str] = Field(default_factory=list)


class QualityRunRequest(BaseModel):
    dataset: str = Field(min_length=1)
    data: list[dict[str, Any]]
    matching_fields: list[str] = Field(default_factory=list)


class QualityRunListItem(BaseModel):
    run_id: str
    dataset: str
    score: float
    risk: str
    created_at: datetime


class QualityRunListResponse(BaseModel):
    runs: list[QualityRunListItem]
