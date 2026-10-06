import json
from typing import Any

from sqlalchemy.orm import Session

from ...models.quality_assessment import QualityAssessment


def persist_quality_assessment(
    db: Session,
    run_id: str,
    dataset: str,
    score: float,
    risk: str,
    rule_count: int,
    failed_rule_count: int,
    rule_scores: list[dict[str, Any]],
) -> QualityAssessment:
    assessment = QualityAssessment(
        run_id=run_id,
        dataset=dataset,
        score=float(score),
        risk=str(risk),
        rule_count=int(rule_count),
        failed_rule_count=int(failed_rule_count),
        rule_scores=json.dumps(rule_scores, default=str),
    )

    db.add(assessment)
    db.flush()

    return assessment


def get_quality_assessment(
    db: Session,
    run_id: str,
) -> QualityAssessment | None:
    return (
        db.query(QualityAssessment)
        .filter(QualityAssessment.run_id == run_id)
        .order_by(QualityAssessment.created_at.desc())
        .first()
    )


def get_quality_assessments(
    db: Session,
    run_id: str,
) -> list[QualityAssessment]:
    return (
        db.query(QualityAssessment)
        .filter(QualityAssessment.run_id == run_id)
        .order_by(QualityAssessment.created_at.desc())
        .all()
    )
