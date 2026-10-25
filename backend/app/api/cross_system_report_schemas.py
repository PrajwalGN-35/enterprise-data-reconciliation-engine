from typing import Any

from pydantic import BaseModel


class CrossSystemReportResponse(BaseModel):
    report_id: str
    schema_version: str
    created_at: str
    report: dict[str, Any]