
from pathlib import Path

import pandas as pd

from app.services.synthetic.source_config import SourceSystemConfig
from app.services.synthetic.source_generator import SourceSystemGenerator
from app.services.synthetic.source_discrepancy import (
    DiscrepancyInjectionConfig,
    SourceDiscrepancyInjector,
)


def create_clean_sources(tmp_path: Path) -> Path:
    output_root = tmp_path

    SourceSystemGenerator().write_all_sources(output_root)

    return output_root / "data" / "enterprise" / "sources"


def test_discrepancy_injector_creates_separate_output(tmp_path):
    source = create_clean_sources(tmp_path)
    output = tmp_path / "sources_discrepant"

    result = SourceDiscrepancyInjector(
        DiscrepancyInjectionConfig(
            source_dir=source,
            output_dir=output,
        )
    ).inject()

    assert len(result["crm_customers"]) == 1001
    assert len(result["erp_customers"]) == 1000
    assert len(result["erp_orders"]) == 2500
    assert len(result["erp_invoices"]) == 2500
    assert len(result["payment_transactions"]) == 2400

    assert (
        output / "crm" / "customers.csv"
    ).exists()
    assert (
        output / "erp" / "customers.csv"
    ).exists()
    assert (
        output / "erp" / "orders.csv"
    ).exists()
    assert (
        output / "erp" / "invoices.csv"
    ).exists()
    assert (
        output / "payment" / "payments.csv"
    ).exists()

    clean = pd.read_csv(
        source / "crm" / "customers.csv"
    )

    assert len(clean) == 1000


def test_discrepancy_injector_is_deterministic(tmp_path):
    source = create_clean_sources(tmp_path)

    first = SourceDiscrepancyInjector(
        DiscrepancyInjectionConfig(
            source_dir=source,
            output_dir=tmp_path / "one",
        )
    ).inject()

    second = SourceDiscrepancyInjector(
        DiscrepancyInjectionConfig(
            source_dir=source,
            output_dir=tmp_path / "two",
        )
    ).inject()

    for key in first:
        pd.testing.assert_frame_equal(
            first[key],
            second[key],
        )


def test_discrepancy_injection_contains_expected_defects(
    tmp_path,
):
    source = create_clean_sources(tmp_path)
    output = tmp_path / "broken"

    result = SourceDiscrepancyInjector(
        DiscrepancyInjectionConfig(
            source_dir=source,
            output_dir=output,
        )
    ).inject()

    crm = result["crm_customers"]
    erp_customers = result["erp_customers"]
    invoices = result["erp_invoices"]
    payments = result["payment_transactions"]

    clean_invoice = pd.read_csv(
        source / "erp" / "invoices.csv"
    )

    assert (
        crm["source_customer_id"].duplicated().sum()
        == 1
    )

    assert (
        "MASTER-CUST-INVALID"
        in set(erp_customers["master_customer_id"])
    )

    assert float(
        invoices.loc[0, "invoice_amount"]
    ) != float(
        clean_invoice.loc[0, "invoice_amount"]
    )

    assert float(
        payments.loc[0, "payment_amount"]
    ) < 0

    assert pd.isna(
        payments.loc[1, "payment_status"]
    )

