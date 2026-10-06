from pathlib import Path

import pandas as pd

from app.services.synthetic.config import SyntheticDataConfig
from app.services.synthetic.generator import SyntheticEnterpriseGenerator


def build_config(tmp_path: Path) -> SyntheticDataConfig:
    return SyntheticDataConfig(
        seed=20261004,
        customer_count=100,
        product_count=25,
        order_count=250,
        invoice_count=250,
        payment_count=240,
        refund_count=25,
        output_directory=str(tmp_path),
    )


def test_generate_all_has_expected_entities(tmp_path):
    generator = SyntheticEnterpriseGenerator(build_config(tmp_path))

    datasets = generator.generate_all()

    assert set(datasets) == {
        "regions",
        "customers",
        "products",
        "orders",
        "invoices",
        "payments",
        "refunds",
    }


def test_record_counts_match_configuration(tmp_path):
    config = build_config(tmp_path)
    datasets = SyntheticEnterpriseGenerator(config).generate_all()

    assert len(datasets["regions"]) == 5
    assert len(datasets["customers"]) == config.customer_count
    assert len(datasets["products"]) == config.product_count
    assert len(datasets["orders"]) == config.order_count
    assert len(datasets["invoices"]) == config.invoice_count
    assert len(datasets["payments"]) == config.payment_count
    assert len(datasets["refunds"]) == config.refund_count


def test_relationships_are_valid(tmp_path):
    datasets = SyntheticEnterpriseGenerator(build_config(tmp_path)).generate_all()

    customers = set(datasets["customers"]["customer_id"])
    products = set(datasets["products"]["product_id"])
    orders = datasets["orders"]

    assert set(orders["customer_id"]).issubset(customers)
    assert set(orders["product_id"]).issubset(products)

    invoices = datasets["invoices"]
    assert set(invoices["order_id"]).issubset(set(orders["order_id"]))
    assert set(invoices["customer_id"]).issubset(customers)

    payments = datasets["payments"]
    assert set(payments["invoice_id"]).issubset(set(invoices["invoice_id"]))
    assert set(payments["customer_id"]).issubset(customers)

    refunds = datasets["refunds"]
    assert set(refunds["order_id"]).issubset(set(orders["order_id"]))
    assert set(refunds["customer_id"]).issubset(customers)


def test_amount_relationships_are_consistent(tmp_path):
    datasets = SyntheticEnterpriseGenerator(build_config(tmp_path)).generate_all()

    orders = datasets["orders"]
    invoices = datasets["invoices"]

    merged = invoices.merge(
        orders[["order_id", "total_amount"]],
        on="order_id",
        suffixes=("_invoice", "_order"),
    )

    assert (
        merged["invoice_amount"].astype(str)
        == merged["total_amount"].astype(str)
    ).all()


def test_generation_is_deterministic(tmp_path):
    config = build_config(tmp_path)

    first = SyntheticEnterpriseGenerator(config).generate_all()
    second = SyntheticEnterpriseGenerator(config).generate_all()

    for name in first:
        pd.testing.assert_frame_equal(first[name], second[name])


def test_write_all_creates_csv_files(tmp_path):
    generator = SyntheticEnterpriseGenerator(build_config(tmp_path))

    paths = generator.write_all()

    assert len(paths) == 7

    for path in paths.values():
        assert path.exists()
        assert path.suffix == ".csv"
        assert pd.read_csv(path).shape[0] > 0
