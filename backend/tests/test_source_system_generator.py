"""Tests for NovaRetail multi-source dataset generation."""

from pathlib import Path

from app.services.synthetic.config import SyntheticDataConfig
from app.services.synthetic.source_config import SourceSystemConfig
from app.services.synthetic.source_generator import SourceSystemGenerator


def test_all_source_datasets_are_generated():
    generator = SourceSystemGenerator()
    datasets = generator.generate_all_sources()

    assert set(datasets) == {
        "crm_customers",
        "erp_customers",
        "erp_orders",
        "erp_invoices",
        "payment_transactions",
    }


def test_source_dataset_counts_match_master_configuration():
    config = SyntheticDataConfig()
    datasets = SourceSystemGenerator(config).generate_all_sources()

    assert len(datasets["crm_customers"]) == config.customer_count
    assert len(datasets["erp_customers"]) == config.customer_count
    assert len(datasets["erp_orders"]) == config.order_count
    assert len(datasets["erp_invoices"]) == config.invoice_count
    assert len(datasets["payment_transactions"]) == config.payment_count


def test_source_ids_are_distinct_from_master_ids():
    datasets = SourceSystemGenerator().generate_all_sources()

    assert all(
        datasets["crm_customers"]["source_customer_id"]
        != datasets["crm_customers"]["master_customer_id"]
    )

    assert all(
        datasets["erp_customers"]["source_customer_id"]
        != datasets["erp_customers"]["master_customer_id"]
    )

    assert all(
        datasets["erp_orders"]["source_order_id"]
        != datasets["erp_orders"]["master_order_id"]
    )


def test_cross_system_relationships_are_preserved():
    datasets = SourceSystemGenerator().generate_all_sources()

    erp_orders = datasets["erp_orders"]
    erp_invoices = datasets["erp_invoices"]
    payments = datasets["payment_transactions"]

    assert set(erp_invoices["order_id"]).issubset(set(erp_orders["master_order_id"]))
    assert set(payments["invoice_id"]).issubset(
        set(erp_invoices["master_invoice_id"])
    )


def test_source_generation_is_deterministic():
    first = SourceSystemGenerator().generate_all_sources()
    second = SourceSystemGenerator().generate_all_sources()

    for name in first:
        assert first[name].equals(second[name])


def test_write_all_sources_creates_expected_files(tmp_path: Path):
    source_config = SourceSystemConfig()
    generator = SourceSystemGenerator(source_config=source_config)

    paths = generator.write_all_sources(tmp_path)

    assert len(paths) == 5
    assert all(path.exists() for path in paths.values())

    assert (
        tmp_path
        / source_config.crm_output_directory
        / "customers.csv"
    ).exists()

    assert (
        tmp_path
        / source_config.erp_output_directory
        / "customers.csv"
    ).exists()

    assert (
        tmp_path
        / source_config.erp_output_directory
        / "orders.csv"
    ).exists()

    assert (
        tmp_path
        / source_config.erp_output_directory
        / "invoices.csv"
    ).exists()

    assert (
        tmp_path
        / source_config.payment_output_directory
        / "payments.csv"
    ).exists()
