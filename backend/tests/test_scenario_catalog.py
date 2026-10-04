from pathlib import Path

from app.services.synthetic.scenario_catalog import ScenarioCatalog
from app.services.synthetic.scenario_config import ScenarioConfig, ScenarioType
from app.services.synthetic.scenario_orchestrator import EnterpriseScenarioOrchestrator


def test_catalog_discovers_clean_and_discrepant_scenarios(
    tmp_path: Path,
) -> None:
    scenario_root = tmp_path / "scenarios"

    EnterpriseScenarioOrchestrator(
        ScenarioConfig(
            scenario=ScenarioType.CLEAN,
            seed=20261004,
            scenario_root=scenario_root,
        )
    ).generate()

    EnterpriseScenarioOrchestrator(
        ScenarioConfig(
            scenario=ScenarioType.DISCREPANT,
            seed=20261004,
            scenario_root=scenario_root,
        )
    ).generate()

    entries = ScenarioCatalog(scenario_root).discover()

    assert len(entries) == 2
    assert {entry.scenario for entry in entries} == {
        "clean",
        "discrepant",
    }


def test_catalog_preserves_validation_metadata(tmp_path: Path) -> None:
    scenario_root = tmp_path / "scenarios"

    clean_result = EnterpriseScenarioOrchestrator(
        ScenarioConfig(
            scenario=ScenarioType.CLEAN,
            seed=20261004,
            scenario_root=scenario_root,
        )
    ).generate()

    discrepant_result = EnterpriseScenarioOrchestrator(
        ScenarioConfig(
            scenario=ScenarioType.DISCREPANT,
            seed=20261004,
            scenario_root=scenario_root,
        )
    ).generate()

    catalog = ScenarioCatalog(scenario_root)

    clean = catalog.get("clean")
    discrepant = catalog.get("discrepant")

    assert clean is not None
    assert discrepant is not None

    assert clean.manifest_path == clean_result.manifest_path
    assert clean.valid is True
    assert clean.error_count == 0
    assert clean.dataset_count == 5

    assert discrepant.manifest_path == discrepant_result.manifest_path
    assert discrepant.valid is False
    assert discrepant.error_count >= 4
    assert discrepant.dataset_count == 5


def test_catalog_returns_empty_for_missing_root(tmp_path: Path) -> None:
    catalog = ScenarioCatalog(tmp_path / "does-not-exist")

    assert catalog.discover() == []
