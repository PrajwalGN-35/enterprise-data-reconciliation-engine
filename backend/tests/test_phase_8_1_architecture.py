from pathlib import Path

import pandas as pd

from app.services.reconciliation.cross_system import (
    CrossSystemDataset,
    run_cross_system_reconciliation,
)
from app.services.reconciliation.reporting import build_cross_system_report
from app.services.synthetic.config import SyntheticDataConfig
from app.services.synthetic.generator import SyntheticEnterpriseGenerator


ARCHITECTURE_DOC = (
    Path(__file__).parents[2]
    / "docs"
    / "phase-8.1-business-impact-architecture.md"
)


def test_phase_8_1_document_defines_financial_and_compatibility_contracts():
    document = ARCHITECTURE_DOC.read_text(encoding="utf-8")

    required_terms = (
        "Python `Decimal`",
        "currency",
        "Observed discrepancy",
        "Potential financial exposure",
        "Estimated business impact",
        "Confirmed financial loss",
        "Double-counting safeguards",
        "Phase 7 discrepancy impact score",
        "explicit identifiers",
        "live SAP, ERP, CRM, payment-gateway",
        "Phase 8.2 through Phase 8.14",
    )

    for term in required_terms:
        assert term in document


def test_phase_8_1_keeps_business_impact_distinct_from_phase_7_impact():
    result = run_cross_system_reconciliation(
        CrossSystemDataset(
            "crm",
            "customers",
            pd.DataFrame([{"source_id": "S-1", "name": "Rahul", "amount": 10}]),
            record_id_field="source_id",
        ),
        CrossSystemDataset(
            "erp",
            "customers",
            pd.DataFrame([{"target_id": "T-1", "name": "Rahul", "amount": 12}]),
            record_id_field="target_id",
        ),
        matching_fields=["name"],
        reconciliation_fields=["amount"],
    )

    report = build_cross_system_report(result, report_id="00000000-0000-0000-0000-000000000001")

    assert "impact_analysis" in report
    assert "business_impact" not in report
    assert report["impact_analysis"]
    assert report["outcomes"][0]["source_reference"]["record_id"] == "S-1"
    assert report["outcomes"][0]["target_reference"]["record_id"] == "T-1"


def test_phase_8_1_uses_explicit_synthetic_currency_and_relationship_facts(tmp_path):
    generator = SyntheticEnterpriseGenerator(
        config=SyntheticDataConfig(
            seed=20261004,
            customer_count=1,
            product_count=1,
            order_count=1,
            invoice_count=1,
            payment_count=1,
            refund_count=1,
            output_directory=str(tmp_path),
        )
    )

    datasets = generator.generate_all()

    assert datasets["orders"]["currency"].eq("INR").all()
    assert datasets["invoices"]["currency"].eq("INR").all()
    assert datasets["payments"]["currency"].eq("INR").all()
    assert set(datasets["invoices"]["order_id"]).issubset(
        set(datasets["orders"]["order_id"])
    )
    assert set(datasets["payments"]["invoice_id"]).issubset(
        set(datasets["invoices"]["invoice_id"])
    )
