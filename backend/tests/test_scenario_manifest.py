from pathlib import Path
import json

from app.services.synthetic.scenario_config import ScenarioConfig, ScenarioType
from app.services.synthetic.scenario_manifest import ScenarioManifestBuilder
from app.services.synthetic.scenario_orchestrator import EnterpriseScenarioOrchestrator


def test_manifest_builder_contains_dataset_metadata(tmp_path: Path) -> None:
    dataset_path = tmp_path / "crm" / "customers.csv"
    dataset_path.parent.mkdir(parents=True)
    dataset_path.write_text("customer_id\n1\n", encoding="utf-8")

    report = {
        "valid": True,
        "dataset_count": 1,
        "row_counts": {"crm_customers": 1},
        "error_count": 0,
        "warning_count": 0,
    }

    manifest = ScenarioManifestBuilder().build(
        scenario="clean",
        seed=20261004,
        source_root=tmp_path,
        dataset_paths={"crm_customers": dataset_path},
        validation_report=report,
    )

    assert manifest["scenario"] == "clean"
    assert manifest["seed"] == 20261004
    assert manifest["validation"]["valid"] is True
    assert manifest["datasets"]["crm_customers"]["row_count"] == 1
    assert manifest["datasets"]["crm_customers"]["exists"] is True


def test_clean_scenario_writes_manifest(tmp_path: Path) -> None:
    config = ScenarioConfig(
        scenario=ScenarioType.CLEAN,
        seed=20261004,
        scenario_root=tmp_path / "scenarios",
    )

    result = EnterpriseScenarioOrchestrator(config).generate()

    assert result.manifest_path.exists()

    manifest = json.loads(
        result.manifest_path.read_text(encoding="utf-8")
    )

    assert manifest["scenario"] == "clean"
    assert manifest["seed"] == 20261004
    assert manifest["validation"]["valid"] is True
    assert manifest["validation"]["error_count"] == 0
    assert len(manifest["datasets"]) == 5


def test_discrepant_scenario_writes_invalid_manifest(tmp_path: Path) -> None:
    config = ScenarioConfig(
        scenario=ScenarioType.DISCREPANT,
        seed=20261004,
        scenario_root=tmp_path / "scenarios",
    )

    result = EnterpriseScenarioOrchestrator(config).generate()

    assert result.manifest_path.exists()

    manifest = json.loads(
        result.manifest_path.read_text(encoding="utf-8")
    )

    assert manifest["scenario"] == "discrepant"
    assert manifest["validation"]["valid"] is False
    assert manifest["validation"]["error_count"] >= 4
    assert len(manifest["datasets"]) == 5
