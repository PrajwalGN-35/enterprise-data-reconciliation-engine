"""Tests for the Phase 5 synthetic enterprise data foundation."""

from app.services.synthetic.config import SyntheticDataConfig
from app.services.synthetic.generator import SyntheticEnterpriseGenerator


def test_generator_is_deterministic():
    config = SyntheticDataConfig(
        customer_count=25,
        product_count=10,
    )

    first = SyntheticEnterpriseGenerator(config)
    second = SyntheticEnterpriseGenerator(config)

    assert first.generate_customers() == second.generate_customers()
    assert first.generate_products() == second.generate_products()


def test_customer_ids_are_unique():
    config = SyntheticDataConfig(customer_count=100)

    generator = SyntheticEnterpriseGenerator(config)
    customers = generator.generate_customers()

    customer_ids = [customer.customer_id for customer in customers]

    assert len(customer_ids) == len(set(customer_ids))
    assert len(customer_ids) == 100


def test_product_ids_are_unique():
    config = SyntheticDataConfig(product_count=50)

    generator = SyntheticEnterpriseGenerator(config)
    products = generator.generate_products()

    product_ids = [product.product_id for product in products]

    assert len(product_ids) == len(set(product_ids))
    assert len(product_ids) == 50


def test_region_structure():
    generator = SyntheticEnterpriseGenerator()
    regions = generator.generate_regions()

    assert len(regions) == 5
    assert all(region.region_id.startswith("REG-") for region in regions)
    assert all(region.country == "India" for region in regions)
