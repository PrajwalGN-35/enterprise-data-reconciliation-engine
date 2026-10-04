from pathlib import Path

from app.services.synthetic.scenario_config import (
    ScenarioConfig,
    ScenarioType,
)
from app.services.synthetic.scenario_orchestrator import (
    EnterpriseScenarioOrchestrator,
)


def test_clean_scenario_is_generated_and_validated(tmp_path):
    config = ScenarioConfig(
        scenario=ScenarioType.CLEAN,
        seed=20261004,
        scenario_root=tmp_path / "scenarios",
    )

    result = EnterpriseScenarioOrchestrator(config).generate()

    assert result.scenario is ScenarioType.CLEAN
    assert result.seed == 20261004
    assert result.source_root.exists()
    assert result.validation_report["valid"] is True
    assert result.validation_report["dataset_count"] == 5
    assert result.validation_report["error_count"] == 0

    assert len(result.dataset_paths) == 5
    assert all(path.exists() for path in result.dataset_paths.values())


def test_discrepant_scenario_is_generated_and_rejected(tmp_path):
    config = ScenarioConfig(
        scenario=ScenarioType.DISCREPANT,
        seed=20261004,
        scenario_root=tmp_path / "scenarios",
    )

    result = EnterpriseScenarioOrchestrator(config).generate()

    assert result.scenario is ScenarioType.DISCREPANT
    assert result.seed == 20261004
    assert result.source_root.exists()
    assert result.validation_report["valid"] is False
    assert result.validation_report["error_count"] >= 4

    assert len(result.dataset_paths) == 5
    assert all(path.exists() for path in result.dataset_paths.values())


def test_scenario_generation_is_deterministic(tmp_path):
    first_config = ScenarioConfig(
        scenario=ScenarioType.CLEAN,
        seed=20261004,
        scenario_root=tmp_path / "first",
    )

    second_config = ScenarioConfig(
        scenario=ScenarioType.CLEAN,
        seed=20261004,
        scenario_root=tmp_path / "second",
    )

    first = EnterpriseScenarioOrchestrator(first_config).generate()
    second = EnterpriseScenarioOrchestrator(second_config).generate()

    for name in first.dataset_paths:
        first_data = first.dataset_paths[name].read_bytes()
        second_data = second.dataset_paths[name].read_bytes()

        assert first_data == second_data


def test_scenario_result_paths_are_under_scenario_root(tmp_path):
    config = ScenarioConfig(
        scenario=ScenarioType.CLEAN,
        scenario_root=tmp_path / "scenarios",
    )

    result = EnterpriseScenarioOrchestrator(config).generate()

    for path in result.dataset_paths.values():
        assert Path(tmp_path / "scenarios") in path.parents
