from app.models.quality_assessment import QualityAssessment
from app.services.data_quality.reconciliation_quality import (
    get_reconciliation_quality,
    get_reconciliation_quality_history,
    record_reconciliation_quality,
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
        self.rows = []

    def add(self, item):
        self.rows.append(item)

    def flush(self):
        pass

    def query(self, *_args):
        return FakeQuery(self.rows)


def test_record_reconciliation_quality():
    db = FakeSession()

    result = record_reconciliation_quality(
        db=db,
        run_id="run-100",
        dataset="erp_customers",
        score=91.5,
        risk="GOOD",
        rule_count=10,
        failed_rule_count=1,
        rule_scores=[
            {"rule_name": "completeness", "score": 100.0},
            {"rule_name": "validity", "score": 83.0},
        ],
    )

    assert isinstance(result, QualityAssessment)
    assert result.run_id == "run-100"
    assert result.score == 91.5
    assert result.risk == "GOOD"


def test_get_reconciliation_quality():
    db = FakeSession()

    assessment = QualityAssessment(
        run_id="run-100",
        dataset="erp_customers",
        score=91.5,
        risk="GOOD",
        rule_count=10,
        failed_rule_count=1,
        rule_scores="[]",
    )

    db.rows.append(assessment)

    assert get_reconciliation_quality(db, "run-100") is assessment


def test_get_reconciliation_quality_history():
    db = FakeSession()

    first = QualityAssessment(
        run_id="run-100",
        dataset="erp_customers",
        score=91.5,
        risk="GOOD",
        rule_count=10,
        failed_rule_count=1,
        rule_scores="[]",
    )

    second = QualityAssessment(
        run_id="run-100",
        dataset="erp_customers",
        score=95.5,
        risk="EXCELLENT",
        rule_count=10,
        failed_rule_count=0,
        rule_scores="[]",
    )

    db.rows.extend([second, first])

    result = get_reconciliation_quality_history(db, "run-100")

    assert len(result) == 2
    assert result[0] is second
    assert result[1] is first
