from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models.quality_run import QualityRun


def persist_quality_run(
    db: Session,
    *,
    dataset: str,
    row_count: int,
    column_count: int,
    rule_count: int,
    failed_rule_count: int,
    score: float,
    risk: str,
    issues: list[dict[str, Any]],
    rule_scores: list[dict[str, Any]],
) -> QualityRun:
    run = QualityRun(
        dataset=dataset,
        row_count=row_count,
        column_count=column_count,
        rule_count=rule_count,
        failed_rule_count=failed_rule_count,
        score=score,
        risk=risk,
        issues_json=json.dumps(issues, default=str),
        rule_scores_json=json.dumps(rule_scores, default=str),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_quality_run(
    db: Session,
    run_id: str,
) -> QualityRun | None:
    return db.get(QualityRun, run_id)


def get_quality_runs(
    db: Session,
    *,
    limit: int = 100,
) -> list[QualityRun]:
    statement = (
        select(QualityRun)
        .order_by(QualityRun.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(statement).all())


def deserialize_quality_run(run: QualityRun) -> dict[str, Any]:
    return {
        "run_id": run.id,
        "dataset": run.dataset,
        "row_count": run.row_count,
        "column_count": run.column_count,
        "rule_count": run.rule_count,
        "failed_rule_count": run.failed_rule_count,
        "score": run.score,
        "risk": run.risk,
        "created_at": run.created_at,
        "rule_scores": json.loads(run.rule_scores_json),
        "issues": json.loads(run.issues_json),
    }
