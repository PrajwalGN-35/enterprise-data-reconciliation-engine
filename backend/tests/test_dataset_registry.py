from pathlib import Path

import pandas as pd
import pytest

from app.services.synthetic.dataset_registry import ScenarioDatasetRegistry
from app.services.synthetic.scenario_catalog import ScenarioCatalog
from app.services.synthetic.scenario_config import ScenarioConfig, ScenarioType
from app.services.synthetic.scenario_orchestrator import EnterpriseScenarioOrchestrator


def create_scenario(tmp_path: Path):
    root = tmp_path / "scenarios"

    EnterpriseScenarioOrchestrator(
        ScenarioConfig(
            scenario=ScenarioType.CLEAN,
            seed=20261004,
            scenario_root=root,
        )
    ).generate()

    entry = ScenarioCatalog(root).get("clean")

    assert entry is not None

    return entry


def test_registry_exposes_all_datasets(tmp_path: Path) -> None:
    scenario = create_scenario(tmp_path)

    registry = ScenarioDatasetRegistry(scenario)
    entries = registry.entries()

    assert len(entries) == 5
    assert {
        entry.name for entry in entries
    } == {
        "crm_customers",
        "erp_customers",
        "erp_orders",
        "erp_invoices",
        "payment_transactions",
    }


def test_registry_contains_source_system_metadata(tmp_path: Path) -> None:
    scenario = create_scenario(tmp_path)

    registry = ScenarioDatasetRegistry(scenario)

    assert registry.get("crm_customers").source_system == "crm"
    assert registry.get("erp_customers").source_system == "erp"
    assert registry.get("erp_orders").source_system == "erp"
    assert registry.get("erp_invoices").source_system == "erp"
    assert (
        registry.get("payment_transactions").source_system
        == "payment"
    )


def test_registry_loads_single_dataset(tmp_path: Path) -> None:
    scenario = create_scenario(tmp_path)

    registry = ScenarioDatasetRegistry(scenario)
    customers = registry.load("crm_customers")

    assert isinstance(customers, pd.DataFrame)
    assert len(customers) == 1000
    assert "customer_name" in customers.columns
    assert "email" in customers.columns


def test_registry_loads_all_datasets(tmp_path: Path) -> None:
    scenario = create_scenario(tmp_path)

    registry = ScenarioDatasetRegistry(scenario)
    datasets = registry.load_all()

    assert len(datasets) == 5
    assert all(isinstance(df, pd.DataFrame) for df in datasets.values())
    assert len(datasets["crm_customers"]) == 1000
    assert len(datasets["erp_customers"]) == 1000
    assert len(datasets["erp_orders"]) == 2500
    assert len(datasets["erp_invoices"]) == 2500
    assert len(datasets["payment_transactions"]) == 2400


def test_registry_rejects_unknown_dataset(tmp_path: Path) -> None:
    scenario = create_scenario(tmp_path)

    registry = ScenarioDatasetRegistry(scenario)

    with pytest.raises(KeyError):
        registry.get("unknown_dataset")
