from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class QualityAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: str
    dataset: str
    score: float = Field(ge=0, le=100)
    risk: str
    rule_count: int = Field(ge=0)
    failed_rule_count: int = Field(ge=0)
    rule_scores: list[dict[str, Any]]
    created_at: datetime


class QualityAssessmentHistoryResponse(BaseModel):
    assessments: list[QualityAssessmentResponse]
    count: int
