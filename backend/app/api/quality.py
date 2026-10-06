from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.quality_schemas import (
    QualityIssueResponse,
    QualityProfileRequest,
    QualityRunListResponse,
    QualityRunRequest,
    QualityRunResponse,
    QualityValidateRequest,
)
from app.core.database import get_db
from app.services.data_quality.engine import DatasetQualityReport
from app.services.data_quality.quality_run_persistence import (
    deserialize_quality_run,
    get_quality_run as fetch_quality_run,
    get_quality_runs,
    persist_quality_run,
)
from app.services.data_quality.scoring import score_quality_report
from app.services.data_quality.workflow_quality import build_standalone_quality_engine


router = APIRouter(prefix="/quality", tags=["Data Quality"])


def _risk_value(risk: Any) -> str:
    return str(getattr(risk, "value", risk))


def _issue_response(issue: Any) -> QualityIssueResponse:
    metadata = getattr(issue, "metadata", None) or {}
    return QualityIssueResponse(
        rule=str(getattr(issue, "rule_name", "")),
        severity=str(
            getattr(
                getattr(issue, "severity", ""),
                "value",
                getattr(issue, "severity", ""),
            )
        ),
        message=str(getattr(issue, "message", "")),
        column=getattr(issue, "column", None),
        row_indices=list(metadata.get("row_indices", ()) or ()),
        affected_rows=int(getattr(issue, "affected_rows", 0) or 0),
        impact=metadata.get("impact"),
        metadata=metadata,
    )


def _report_response(
    report: DatasetQualityReport,
    *,
    run_id: str | None = None,
    created_at: Any = None,
) -> QualityRunResponse:
    score = score_quality_report(report)
    return QualityRunResponse(
        run_id=run_id,
        dataset=report.dataset,
        row_count=report.row_count,
        column_count=report.column_count,
        rule_count=score["rule_count"],
        failed_rule_count=score["failed_rule_count"],
        score=float(score["score"]),
        risk=_risk_value(score["risk"]),
        created_at=created_at,
        rule_scores=[
            {
                "rule": item["rule_name"],
                "score": float(item["score"]),
                "impact": float(item["impact"]),
                "issue_count": int(item["issue_count"]),
                "affected_rows": int(item["affected_rows"]),
            }
            for item in score["rules"]
        ],
        issues=[
            _issue_response(issue)
            for result in report.results
            for issue in result.issues
        ],
    )


def _execute_quality(
    dataset: str,
    data: list[dict[str, Any]],
    matching_fields: list[str],
) -> DatasetQualityReport:
    dataframe = pd.DataFrame(data)
    engine = build_standalone_quality_engine(
        dataframe=dataframe,
        matching_fields=matching_fields,
    )
    return engine.run(
        dataframe=dataframe,
        dataset=dataset,
    )


@router.post("/profile", response_model=QualityRunResponse)
def profile_quality(request: QualityProfileRequest) -> QualityRunResponse:
    try:
        return _report_response(
            _execute_quality(
                request.dataset,
                request.data,
                request.matching_fields,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/validate", response_model=QualityRunResponse)
def validate_quality(request: QualityValidateRequest) -> QualityRunResponse:
    try:
        return _report_response(
            _execute_quality(
                request.dataset,
                request.data,
                request.matching_fields,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/run", response_model=QualityRunResponse)
def run_quality(
    request: QualityRunRequest,
    db: Session = Depends(get_db),
) -> QualityRunResponse:
    try:
        report = _execute_quality(
            request.dataset,
            request.data,
            request.matching_fields,
        )
        response = _report_response(report)

        run = persist_quality_run(
            db,
            dataset=response.dataset,
            row_count=response.row_count,
            column_count=response.column_count,
            rule_count=response.rule_count,
            failed_rule_count=response.failed_rule_count,
            score=response.score,
            risk=response.risk,
            issues=[issue.model_dump() for issue in response.issues],
            rule_scores=response.rule_scores,
        )

        return _report_response(
            report,
            run_id=run.id,
            created_at=run.created_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runs", response_model=QualityRunListResponse)
def list_quality_runs(
    db: Session = Depends(get_db),
) -> QualityRunListResponse:
    return QualityRunListResponse(
        runs=[
            {
                "run_id": run.id,
                "dataset": run.dataset,
                "score": run.score,
                "risk": run.risk,
                "created_at": run.created_at,
            }
            for run in get_quality_runs(db)
        ]
    )


@router.get("/runs/{run_id}", response_model=QualityRunResponse)
def get_quality_run(
    run_id: str,
    db: Session = Depends(get_db),
) -> QualityRunResponse:
    run = fetch_quality_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Quality run not found.")
    data = deserialize_quality_run(run)
    return QualityRunResponse(**data)


@router.get("/runs/{run_id}/issues", response_model=list[QualityIssueResponse])
def get_quality_run_issues(
    run_id: str,
    db: Session = Depends(get_db),
) -> list[QualityIssueResponse]:
    run = fetch_quality_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Quality run not found.")
    data = deserialize_quality_run(run)
    return [QualityIssueResponse(**issue) for issue in data["issues"]]


@router.get("/runs/{run_id}/score")
def get_quality_run_score(
    run_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    run = fetch_quality_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Quality run not found.")
    return {
        "run_id": run.id,
        "dataset": run.dataset,
        "score": run.score,
        "risk": run.risk,
        "rule_count": run.rule_count,
        "failed_rule_count": run.failed_rule_count,
        "rule_scores": deserialize_quality_run(run)["rule_scores"],
    }
