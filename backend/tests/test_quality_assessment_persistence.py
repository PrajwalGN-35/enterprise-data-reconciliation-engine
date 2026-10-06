from datetime import datetime, timezone

from app.models.quality_assessment import QualityAssessment
from app.services.data_quality.persistence import (
    get_quality_assessment,
    get_quality_assessments,
    persist_quality_assessment,
)


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *_args):
        return self

    def order_by(self, *_args):
        return self

    def first(self):
        return self.rows[0] if self.rows else None

    def all(self):
        return self.rows


class FakeSession:
    def __init__(self):
        self.added = []
        self.flushed = False
        self.rows = []

    def add(self, item):
        self.added.append(item)
        self.rows.append(item)

    def flush(self):
        self.flushed = True

    def query(self, *_args):
        return FakeQuery(self.rows)


def test_persist_quality_assessment_creates_record():
    db = FakeSession()

    assessment = persist_quality_assessment(
        db=db,
        run_id="run-001",
        dataset="erp_customers",
        score=92.5,
        risk="GOOD",
        rule_count=8,
        failed_rule_count=1,
        rule_scores=[
            {"rule_name": "completeness", "score": 100.0},
            {"rule_name": "validity", "score": 85.0},
        ],
    )

    assert assessment.run_id == "run-001"
    assert assessment.dataset == "erp_customers"
    assert assessment.score == 92.5
    assert assessment.risk == "GOOD"
    assert assessment.rule_count == 8
    assert assessment.failed_rule_count == 1
    assert '"rule_name": "completeness"' in assessment.rule_scores
    assert db.added == [assessment]
    assert db.flushed is True


def test_get_latest_quality_assessment():
    db = FakeSession()

    first = QualityAssessment(
        run_id="run-001",
        dataset="erp_customers",
        score=80.0,
        risk="FAIR",
        rule_count=5,
        failed_rule_count=2,
        rule_scores="[]",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    second = QualityAssessment(
        run_id="run-001",
        dataset="erp_customers",
        score=95.0,
        risk="EXCELLENT",
        rule_count=5,
        failed_rule_count=0,
        rule_scores="[]",
        created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    db.rows = [second, first]

    result = get_quality_assessment(db, "run-001")

    assert result is second


def test_get_quality_assessments_returns_history():
    db = FakeSession()

    first = QualityAssessment(
        run_id="run-001",
        dataset="erp_customers",
        score=80.0,
        risk="FAIR",
        rule_count=5,
        failed_rule_count=2,
        rule_scores="[]",
    )

    second = QualityAssessment(
        run_id="run-001",
        dataset="erp_customers",
        score=95.0,
        risk="EXCELLENT",
        rule_count=5,
        failed_rule_count=0,
        rule_scores="[]",
    )

    db.rows = [second, first]

    result = get_quality_assessments(db, "run-001")

    assert result == [second, first]
    assert len(result) == 2
