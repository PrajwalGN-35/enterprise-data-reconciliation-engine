"""Configuration for deterministic NovaRetail synthetic data."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SyntheticDataConfig:
    """Global configuration for synthetic enterprise datasets."""

    company_name: str = "NovaRetail Enterprise"
    seed: int = 20261004

    customer_count: int = 1000
    product_count: int = 250
    order_count: int = 2500
    invoice_count: int = 2500
    payment_count: int = 2400
    refund_count: int = 250

    output_directory: str = "data/enterprise"
