def test_quality_workflow_runtime_imports_use_single_model_registry():
    from app.core.database import Base
    import app.models  # noqa: F401
    import app.services.data_quality.workflow_quality  # noqa: F401
    import app.services.data_quality.persistence  # noqa: F401
    import app.services.data_quality.reconciliation_quality  # noqa: F401

    # The application runtime uses the `app.*` namespace because backend/
    # is placed on PYTHONPATH. Verify that the quality workflow modules
    # register the expected models into the same SQLAlchemy metadata object.
    assert "reconciliation_runs" in Base.metadata.tables
    assert "quality_assessments" in Base.metadata.tables
    assert "audit_logs" in Base.metadata.tables

    reconciliation_table = Base.metadata.tables["reconciliation_runs"]
    quality_table = Base.metadata.tables["quality_assessments"]

    assert reconciliation_table is not quality_table
    assert quality_table.name == "quality_assessments"
