"""Deterministic synthetic enterprise data generator foundation."""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

from .config import SyntheticDataConfig
from .models import Customer, Product, Region


class SyntheticEnterpriseGenerator:
    """Generate deterministic synthetic NovaRetail master data."""

    def __init__(self, config: SyntheticDataConfig | None = None) -> None:
        self.config = config or SyntheticDataConfig()
        self.random = random.Random(self.config.seed)

    def generate_regions(self) -> list[Region]:
        """Generate the enterprise's geographic regions."""

        regions = [
            Region("REG-001", "South", "India"),
            Region("REG-002", "West", "India"),
            Region("REG-003", "North", "India"),
            Region("REG-004", "East", "India"),
            Region("REG-005", "Central", "India"),
        ]

        return regions

    def generate_customers(self) -> list[Customer]:
        """Generate deterministic synthetic customer master records."""

        regions = self.generate_regions()
        customers: list[Customer] = []

        first_names = [
            "Aarav",
            "Ananya",
            "Arjun",
            "Diya",
            "Ishaan",
            "Kavya",
            "Meera",
            "Rahul",
            "Riya",
            "Vikram",
        ]

        last_names = [
            "Sharma",
            "Patel",
            "Reddy",
            "Nair",
            "Iyer",
            "Gupta",
            "Mehta",
            "Rao",
            "Singh",
            "Joshi",
        ]

        statuses = ["ACTIVE", "ACTIVE", "ACTIVE", "INACTIVE"]

        for index in range(1, self.config.customer_count + 1):
            customer_id = f"CUST-{index:06d}"
            first_name = self.random.choice(first_names)
            last_name = self.random.choice(last_names)
            full_name = f"{first_name} {last_name}"

            email = (
                f"{first_name.lower()}.{last_name.lower()}"
                f"{index}@novaretail.example"
            )

            phone = f"+91{9000000000 + index:010d}"

            region = self.random.choice(regions)

            customers.append(
                Customer(
                    customer_id=customer_id,
                    customer_name=full_name,
                    email=email,
                    phone=phone,
                    region_id=region.region_id,
                    customer_status=self.random.choice(statuses),
                )
            )

        return customers

    def generate_products(self) -> list[Product]:
        """Generate deterministic synthetic product master records."""

        categories = [
            "Electronics",
            "Home Appliances",
            "Fashion",
            "Grocery",
            "Beauty",
            "Sports",
            "Furniture",
        ]

        products: list[Product] = []

        for index in range(1, self.config.product_count + 1):
            category = self.random.choice(categories)

            unit_price = Decimal(
                str(round(self.random.uniform(299, 99999), 2))
            )

            products.append(
                Product(
                    product_id=f"PROD-{index:06d}",
                    product_name=f"{category} Product {index:04d}",
                    category=category,
                    unit_price=unit_price,
                    product_status=self.random.choice(
                        ["ACTIVE", "ACTIVE", "ACTIVE", "DISCONTINUED"]
                    ),
                )
            )

        return products

    @staticmethod
    def random_date(
        rng: random.Random,
        start: date = date(2025, 1, 1),
        end: date = date(2026, 9, 30),
    ) -> date:
        """Return a deterministic random date within a fixed period."""

        days = (end - start).days
        return start + timedelta(days=rng.randint(0, days))
