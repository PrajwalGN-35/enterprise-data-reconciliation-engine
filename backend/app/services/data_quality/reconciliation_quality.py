from typing import Any

from sqlalchemy.orm import Session

from .persistence import (
    get_quality_assessment,
    get_quality_assessments,
    persist_quality_assessment,
)


def record_reconciliation_quality(
    db: Session,
    run_id: str,
    dataset: str,
    score: float,
    risk: str,
    rule_count: int,
    failed_rule_count: int,
    rule_scores: list[dict[str, Any]],
):
    return persist_quality_assessment(
        db=db,
        run_id=run_id,
        dataset=dataset,
        score=score,
        risk=risk,
        rule_count=rule_count,
        failed_rule_count=failed_rule_count,
        rule_scores=rule_scores,
    )


def get_reconciliation_quality(db: Session, run_id: str):
    return get_quality_assessment(db, run_id)


def get_reconciliation_quality_history(db: Session, run_id: str):
    return get_quality_assessments(db, run_id)
