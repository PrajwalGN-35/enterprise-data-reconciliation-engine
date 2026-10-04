
from pathlib import Path

import pandas as pd

from app.services.synthetic.source_config import SourceSystemConfig
from app.services.synthetic.source_generator import SourceSystemGenerator
from app.services.synthetic.source_discrepancy import (
    DiscrepancyInjectionConfig,
    SourceDiscrepancyInjector,
)
from app.services.synthetic.source_validator import (
    SourceDataValidator,
)


def create_clean_sources(tmp_path: Path) -> Path:
    output_root = tmp_path

    SourceSystemGenerator().write_all_sources(output_root)

    return output_root / "data" / "enterprise" / "sources"


def test_clean_source_data_passes_validation(tmp_path):
    source = create_clean_sources(tmp_path)

    report = SourceDataValidator(source).validate()

    assert report["valid"] is True
    assert report["dataset_count"] == 5
    assert report["error_count"] == 0


def test_corrupted_source_data_is_rejected(tmp_path):
    source = create_clean_sources(tmp_path)
    output = tmp_path / "sources_discrepant"

    SourceDiscrepancyInjector(
        DiscrepancyInjectionConfig(
            source_dir=source,
            output_dir=output,
        )
    ).inject()

    report = SourceDataValidator(output).validate()

    assert report["valid"] is False
    assert report["error_count"] >= 4

    rules = {
        issue.rule
        for issue in report["issues"]
    }

    assert "duplicate_key" in rules
    assert "referential_integrity" in rules
    assert "required_field" in rules
    assert "financial_sanity" in rules


def test_validator_detects_non_numeric_amount(tmp_path):
    source = tmp_path / "sources"

    for system in (
        "crm",
        "erp",
        "payment",
    ):
        (source / system).mkdir(
            parents=True
        )

    customer_columns = [
        "source_customer_id",
        "master_customer_id",
        "customer_name",
        "email",
        "phone",
        "city",
        "region_id",
        "customer_status",
    ]

    customer = [
        [
            "CRM-CUST-C1",
            "C1",
            "Test",
            "test@example.com",
            "999",
            "Bengaluru",
            "R1",
            "ACTIVE",
        ]
    ]

    pd.DataFrame(
        customer,
        columns=customer_columns,
    ).to_csv(
        source / "crm/customers.csv",
        index=False,
    )

    pd.DataFrame(
        customer,
        columns=customer_columns,
    ).to_csv(
        source / "erp/customers.csv",
        index=False,
    )

    pd.DataFrame(
        [
            [
                "ERP-ORD-O1",
                "O1",
                "C1",
                "P1",
                "2026-01-01",
                1,
                "bad",
                "COMPLETED",
            ]
        ],
        columns=[
            "source_order_id",
            "master_order_id",
            "customer_id",
            "product_id",
            "order_date",
            "quantity",
            "total_amount",
            "order_status",
        ],
    ).to_csv(
        source / "erp/orders.csv",
        index=False,
    )

    pd.DataFrame(
        [
            [
                "ERP-INV-I1",
                "I1",
                "O1",
                "C1",
                "2026-01-01",
                10,
                "ISSUED",
            ]
        ],
        columns=[
            "source_invoice_id",
            "master_invoice_id",
            "order_id",
            "customer_id",
            "invoice_date",
            "invoice_amount",
            "invoice_status",
        ],
    ).to_csv(
        source / "erp/invoices.csv",
        index=False,
    )

    pd.DataFrame(
        [
            [
                "PAY-TXN-P1",
                "P1",
                "I1",
                "C1",
                "2026-01-01",
                10,
                "UPI",
                "SUCCESS",
            ]
        ],
        columns=[
            "source_payment_id",
            "master_payment_id",
            "invoice_id",
            "customer_id",
            "payment_date",
            "payment_amount",
            "payment_method",
            "payment_status",
        ],
    ).to_csv(
        source / "payment/payments.csv",
        index=False,
    )

    report = SourceDataValidator(source).validate()

    assert report["valid"] is False
    assert any(
        issue.rule == "data_type"
        and "total_amount" in issue.message
        for issue in report["issues"]
    )

