from pathlib import Path

from app.services.synthetic.dataset_profiler import DatasetProfiler
from app.services.synthetic.dataset_registry import ScenarioDatasetRegistry
from app.services.synthetic.scenario_catalog import ScenarioCatalog
from app.services.synthetic.scenario_config import ScenarioConfig, ScenarioType
from app.services.synthetic.scenario_orchestrator import EnterpriseScenarioOrchestrator


def create_registry(tmp_path: Path) -> ScenarioDatasetRegistry:
    scenario_root = tmp_path / "scenarios"

    EnterpriseScenarioOrchestrator(
        ScenarioConfig(
            scenario=ScenarioType.CLEAN,
            seed=20261004,
            scenario_root=scenario_root,
        )
    ).generate()

    scenario = ScenarioCatalog(scenario_root).get("clean")

    assert scenario is not None

    return ScenarioDatasetRegistry(scenario)


def test_profiles_customer_dataset(tmp_path: Path) -> None:
    registry = create_registry(tmp_path)

    profile = DatasetProfiler(registry).profile("crm_customers")

    assert profile.name == "crm_customers"
    assert profile.source_system == "crm"
    assert profile.row_count == 1000
    assert profile.column_count == 8

    names = {column.name for column in profile.columns}

    assert "customer_name" in names
    assert "email" in names
    assert "phone" in names


def test_clean_customer_dataset_has_no_nulls(tmp_path: Path) -> None:
    registry = create_registry(tmp_path)

    profile = DatasetProfiler(registry).profile("crm_customers")

    assert all(column.null_count == 0 for column in profile.columns)
    assert all(column.null_rate == 0.0 for column in profile.columns)


def test_profiles_all_datasets(tmp_path: Path) -> None:
    registry = create_registry(tmp_path)

    profiles = DatasetProfiler(registry).profile_all()

    assert len(profiles) == 5

    assert profiles["crm_customers"].row_count == 1000
    assert profiles["erp_customers"].row_count == 1000
    assert profiles["erp_orders"].row_count == 2500
    assert profiles["erp_invoices"].row_count == 2500
    assert profiles["payment_transactions"].row_count == 2400


def test_profile_to_dict_is_json_compatible(tmp_path: Path) -> None:
    registry = create_registry(tmp_path)

    profile = DatasetProfiler(registry).profile("crm_customers")
    payload = DatasetProfiler.to_dict(profile)

    assert payload["name"] == "crm_customers"
    assert payload["row_count"] == 1000
    assert payload["column_count"] == 8
    assert len(payload["columns"]) == 8

    for column in payload["columns"]:
        assert {
            "name",
            "dtype",
            "row_count",
            "null_count",
            "null_rate",
            "unique_count",
        } <= column.keys()
