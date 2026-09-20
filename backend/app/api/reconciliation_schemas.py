from typing import Any

from pydantic import BaseModel, Field


class ReconciliationRunResponse(BaseModel):
    status: str
    source_file_name: str
    target_file_name: str
    schema_comparison: dict[str, Any]
    matches: list[dict[str, Any]]
    reconciliation_results: list[dict[str, Any]]
    summary: dict[str, Any]


class ReconciliationRunRequest(BaseModel):
    matching_fields: list[str] = Field(min_length=1)
    reconciliation_fields: list[str] = Field(min_length=1)
