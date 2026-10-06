from app.models import QualityAssessment, ReconciliationRun


def test_quality_assessment_model_metadata():
    assert QualityAssessment.__tablename__ == "quality_assessments"

    columns = {
        column.name
        for column in QualityAssessment.__table__.columns
    }

    assert columns == {
        "id",
        "run_id",
        "dataset",
        "score",
        "risk",
        "rule_count",
        "failed_rule_count",
        "rule_scores",
        "created_at",
    }


def test_quality_assessment_links_to_reconciliation_run():
    foreign_keys = {
        foreign_key.target_fullname
        for foreign_key in QualityAssessment.__table__.c.run_id.foreign_keys
    }

    assert "reconciliation_runs.id" in foreign_keys
    assert hasattr(ReconciliationRun, "quality_assessments")


def test_quality_assessment_relationship_configuration():
    relationship = QualityAssessment.reconciliation_run.property

    assert relationship.back_populates == "quality_assessments"
    assert relationship.key == "reconciliation_run"


def test_quality_assessment_defaults_are_defined():
    assert QualityAssessment.__table__.c.rule_scores.default.arg == "[]"
    assert QualityAssessment.__table__.c.rule_count.default.arg == 0
    assert QualityAssessment.__table__.c.failed_rule_count.default.arg == 0
