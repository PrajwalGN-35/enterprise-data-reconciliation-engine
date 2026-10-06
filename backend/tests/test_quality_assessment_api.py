from datetime import datetime, timezone

from app.models.quality_assessment import QualityAssessment
from app.models.reconciliation import ReconciliationRun


def _run(run_id="run-quality-001"):
    return ReconciliationRun(
        id=run_id,
        source_file_name="source.csv",
        target_file_name="target.csv",
        status="completed",
        started_at=datetime.now(timezone.utc),
    )


def _assessment(run_id="run-quality-001"):
    return QualityAssessment(
        run_id=run_id,
        dataset="erp_customers",
        score=94.5,
        risk="GOOD",
        rule_count=10,
        failed_rule_count=1,
        rule_scores='[{"rule_name":"completeness","score":100.0}]',
        created_at=datetime.now(timezone.utc),
    )


def test_quality_assessment_response_schema_serializes():
    from app.api.quality_assessment_schemas import QualityAssessmentResponse

    assessment = _assessment()

    response = QualityAssessmentResponse(
        id=1,
        run_id=assessment.run_id,
        dataset=assessment.dataset,
        score=assessment.score,
        risk=assessment.risk,
        rule_count=assessment.rule_count,
        failed_rule_count=assessment.failed_rule_count,
        rule_scores=[
            {"rule_name": "completeness", "score": 100.0}
        ],
        created_at=assessment.created_at,
    )

    assert response.score == 94.5
    assert response.risk == "GOOD"
    assert response.rule_scores[0]["rule_name"] == "completeness"


def test_quality_assessment_history_response_schema():
    from app.api.quality_assessment_schemas import (
        QualityAssessmentHistoryResponse,
        QualityAssessmentResponse,
    )

    assessment = _assessment()

    item = QualityAssessmentResponse(
        id=1,
        run_id=assessment.run_id,
        dataset=assessment.dataset,
        score=assessment.score,
        risk=assessment.risk,
        rule_count=assessment.rule_count,
        failed_rule_count=assessment.failed_rule_count,
        rule_scores=[],
        created_at=assessment.created_at,
    )

    response = QualityAssessmentHistoryResponse(
        assessments=[item],
        count=1,
    )

    assert response.count == 1
    assert len(response.assessments) == 1
