from pathlib import Path

from app.services.synthetic.scenario_config import (
    ScenarioConfig,
    ScenarioType,
)


def test_clean_scenario_configuration():
    config = ScenarioConfig(
        scenario=ScenarioType.CLEAN,
        scenario_root=Path("test-output"),
    )

    assert config.scenario is ScenarioType.CLEAN
    assert config.seed == 20261004
    assert (
        config.active_source_root
        == Path(
            "test-output/clean/data/enterprise/sources"
        )
    )


def test_discrepant_scenario_configuration():
    config = ScenarioConfig(
        scenario=ScenarioType.DISCREPANT,
        scenario_root=Path("test-output"),
    )

    assert config.scenario is ScenarioType.DISCREPANT
    assert (
        config.active_source_root
        == Path(
            "test-output/discrepant/"
            "data/enterprise/sources_discrepant"
        )
    )


def test_scenario_types_are_stable():
    assert ScenarioType.CLEAN.value == "clean"
    assert ScenarioType.DISCREPANT.value == "discrepant"
