from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
import random
from pathlib import Path

import pandas as pd

from .config import SyntheticDataConfig


class SyntheticEnterpriseGenerator:
    """Generate deterministic, relational synthetic enterprise master data."""

    FIRST_NAMES = [
        "Aarav", "Aditi", "Aditya", "Akash", "Ananya", "Arjun", "Arnav",
        "Diya", "Ishaan", "Kavya", "Kiran", "Meera", "Neha", "Nikhil",
        "Pooja", "Rahul", "Riya", "Rohan", "Sahana", "Sanjay", "Sneha",
        "Tanvi", "Varun", "Vikram", "Vivek", "Yash",
    ]

    LAST_NAMES = [
        "Sharma", "Patel", "Reddy", "Nair", "Iyer", "Rao", "Mehta",
        "Kapoor", "Joshi", "Menon", "Kulkarni", "Desai", "Shah", "Gupta",
        "Bhat", "Shetty", "Verma", "Singh", "Kumar", "Das",
    ]

    REGIONS = [
        {
            "region_id": "REG-NORTH",
            "region_name": "North India",
            "country": "India",
            "currency": "INR",
        },
        {
            "region_id": "REG-SOUTH",
            "region_name": "South India",
            "country": "India",
            "currency": "INR",
        },
        {
            "region_id": "REG-EAST",
            "region_name": "East India",
            "country": "India",
            "currency": "INR",
        },
        {
            "region_id": "REG-WEST",
            "region_name": "West India",
            "country": "India",
            "currency": "INR",
        },
        {
            "region_id": "REG-CENTRAL",
            "region_name": "Central India",
            "country": "India",
            "currency": "INR",
        },
    ]

    CATEGORIES = [
        "Electronics",
        "Home Appliances",
        "Furniture",
        "Mobile Accessories",
        "Office Supplies",
        "Personal Care",
        "Kitchen",
        "Sports & Fitness",
    ]

    CITIES_BY_REGION = {
        "REG-NORTH": ["Delhi", "Jaipur", "Chandigarh", "Lucknow"],
        "REG-SOUTH": ["Bengaluru", "Chennai", "Hyderabad", "Kochi"],
        "REG-EAST": ["Kolkata", "Bhubaneswar", "Patna", "Ranchi"],
        "REG-WEST": ["Mumbai", "Pune", "Ahmedabad", "Surat"],
        "REG-CENTRAL": ["Bhopal", "Indore", "Nagpur", "Raipur"],
    }

    PRODUCT_NAMES = {
        "Electronics": [
            "Smart Monitor", "Wireless Speaker", "Bluetooth Headset",
            "Mechanical Keyboard", "USB-C Hub",
        ],
        "Home Appliances": [
            "Air Purifier", "Mixer Grinder", "Electric Kettle",
            "Robot Vacuum", "Induction Cooktop",
        ],
        "Furniture": [
            "Office Chair", "Study Desk", "Bookshelf", "Storage Cabinet",
            "Standing Desk",
        ],
        "Mobile Accessories": [
            "Fast Charger", "Power Bank", "Wireless Charger",
            "Phone Stand", "USB-C Cable",
        ],
        "Office Supplies": [
            "Printer Paper", "Notebook Pack", "Desk Organizer",
            "Whiteboard", "Document Scanner",
        ],
        "Personal Care": [
            "Electric Trimmer", "Hair Dryer", "Grooming Kit",
            "Skin Care Set", "Digital Scale",
        ],
        "Kitchen": [
            "Cookware Set", "Food Processor", "Water Bottle",
            "Storage Container Set", "Coffee Maker",
        ],
        "Sports & Fitness": [
            "Yoga Mat", "Resistance Bands", "Dumbbell Set",
            "Fitness Tracker", "Sports Backpack",
        ],
    }

    PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Net Banking"]
    CUSTOMER_STATUSES = ["ACTIVE", "ACTIVE", "ACTIVE", "INACTIVE", "SUSPENDED"]
    ORDER_STATUSES = ["CONFIRMED", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"]
    INVOICE_STATUSES = ["ISSUED", "ISSUED", "PAID", "OVERDUE", "CANCELLED"]
    PAYMENT_STATUSES = ["SUCCESS", "SUCCESS", "SUCCESS", "PENDING", "FAILED"]

    def __init__(self, config: SyntheticDataConfig | None = None):
        self.config = config or SyntheticDataConfig()
        self.random = random.Random(self.config.seed)

        self._regions: list[dict] = []
        self._customers: list[dict] = []
        self._products: list[dict] = []
        self._orders: list[dict] = []
        self._invoices: list[dict] = []
        self._payments: list[dict] = []
        self._refunds: list[dict] = []

    def generate_regions(self) -> list[dict]:
        self._regions = [dict(region) for region in self.REGIONS]
        return self._regions

    def _random_date(self) -> date:
        start = date(2025, 1, 1)
        end = date(2026, 9, 30)
        days = (end - start).days
        return start + timedelta(days=self.random.randint(0, days))

    def random_date(self) -> date:
        return self._random_date()

    def _phone(self) -> str:
        return f"+91-{self.random.randint(7000000000, 9999999999)}"

    def _email(self, first: str, last: str, customer_id: int) -> str:
        return f"{first.lower()}.{last.lower()}{customer_id}@novaretail.example"

    def generate_customers(self) -> list[dict]:
        if not self._regions:
            self.generate_regions()

        self._customers = []

        for number in range(1, self.config.customer_count + 1):
            first = self.random.choice(self.FIRST_NAMES)
            last = self.random.choice(self.LAST_NAMES)
            region = self.random.choice(self._regions)
            city = self.random.choice(
                self.CITIES_BY_REGION[region["region_id"]]
            )

            self._customers.append(
                {
                    "customer_id": f"CUST-{number:06d}",
                    "customer_name": f"{first} {last}",
                    "email": self._email(first, last, number),
                    "phone": self._phone(),
                    "city": city,
                    "region_id": region["region_id"],
                    "customer_status": self.random.choice(
                        self.CUSTOMER_STATUSES
                    ),
                    "created_date": self._random_date().isoformat(),
                }
            )

        return self._customers

    def generate_products(self) -> list[dict]:
        self._products = []

        for number in range(1, self.config.product_count + 1):
            category = self.random.choice(self.CATEGORIES)
            base_name = self.random.choice(self.PRODUCT_NAMES[category])

            self._products.append(
                {
                    "product_id": f"PROD-{number:06d}",
                    "product_name": f"{base_name} {number:03d}",
                    "category": category,
                    "unit_price": str(
                        Decimal(str(round(self.random.uniform(299, 49999), 2)))
                    ),
                    "currency": "INR",
                    "product_status": (
                        "ACTIVE" if self.random.random() < 0.92 else "DISCONTINUED"
                    ),
                }
            )

        return self._products

    def generate_orders(self) -> list[dict]:
        if not self._customers:
            self.generate_customers()

        if not self._products:
            self.generate_products()

        self._orders = []

        for number in range(1, self.config.order_count + 1):
            customer = self.random.choice(self._customers)
            product = self.random.choice(self._products)

            quantity = self.random.choices(
                [1, 2, 3, 4, 5],
                weights=[55, 25, 12, 6, 2],
                k=1,
            )[0]

            unit_price = Decimal(product["unit_price"])
            total_amount = (unit_price * quantity).quantize(Decimal("0.01"))

            self._orders.append(
                {
                    "order_id": f"ORD-{number:07d}",
                    "customer_id": customer["customer_id"],
                    "product_id": product["product_id"],
                    "order_date": self._random_date().isoformat(),
                    "quantity": quantity,
                    "unit_price": str(unit_price),
                    "total_amount": str(total_amount),
                    "currency": "INR",
                    "order_status": self.random.choice(self.ORDER_STATUSES),
                }
            )

        return self._orders

    def generate_invoices(self) -> list[dict]:
        if not self._orders:
            self.generate_orders()

        self._invoices = []

        for number, order in enumerate(
            self._orders[: self.config.invoice_count], start=1
        ):
            invoice_date = date.fromisoformat(order["order_date"]) + timedelta(
                days=self.random.randint(0, 5)
            )

            self._invoices.append(
                {
                    "invoice_id": f"INV-{number:07d}",
                    "order_id": order["order_id"],
                    "customer_id": order["customer_id"],
                    "invoice_date": invoice_date.isoformat(),
                    "invoice_amount": order["total_amount"],
                    "currency": "INR",
                    "invoice_status": self.random.choice(self.INVOICE_STATUSES),
                }
            )

        return self._invoices

    def generate_payments(self) -> list[dict]:
        if not self._invoices:
            self.generate_invoices()

        self._payments = []

        for number, invoice in enumerate(
            self._invoices[: self.config.payment_count], start=1
        ):
            payment_date = date.fromisoformat(invoice["invoice_date"]) + timedelta(
                days=self.random.randint(0, 7)
            )

            self._payments.append(
                {
                    "payment_id": f"PAY-{number:07d}",
                    "invoice_id": invoice["invoice_id"],
                    "customer_id": invoice["customer_id"],
                    "payment_date": payment_date.isoformat(),
                    "payment_amount": invoice["invoice_amount"],
                    "payment_method": self.random.choice(self.PAYMENT_METHODS),
                    "payment_status": self.random.choice(self.PAYMENT_STATUSES),
                    "currency": "INR",
                }
            )

        return self._payments

    def generate_refunds(self) -> list[dict]:
        if not self._customers:
            self.generate_customers()

        if not self._orders:
            self.generate_orders()

        self._refunds = []

        for number in range(1, self.config.refund_count + 1):
            order = self.random.choice(self._orders)
            customer_id = order["customer_id"]

            order_date = date.fromisoformat(order["order_date"])
            refund_date = order_date + timedelta(
                days=self.random.randint(3, 30)
            )

            order_amount = Decimal(order["total_amount"])
            refund_amount = (
                order_amount * Decimal(str(self.random.uniform(0.1, 0.8)))
            ).quantize(Decimal("0.01"))

            self._refunds.append(
                {
                    "refund_id": f"REF-{number:07d}",
                    "order_id": order["order_id"],
                    "customer_id": customer_id,
                    "refund_date": refund_date.isoformat(),
                    "refund_amount": str(refund_amount),
                    "refund_reason": self.random.choice(
                        [
                            "CUSTOMER_REQUEST",
                            "DAMAGED_ITEM",
                            "WRONG_ITEM",
                            "DELIVERY_ISSUE",
                        ]
                    ),
                    "currency": "INR",
                }
            )

        return self._refunds

    def generate_all(self) -> dict[str, pd.DataFrame]:
        self.generate_regions()
        self.generate_customers()
        self.generate_products()
        self.generate_orders()
        self.generate_invoices()
        self.generate_payments()
        self.generate_refunds()

        return {
            "regions": pd.DataFrame(self._regions),
            "customers": pd.DataFrame(self._customers),
            "products": pd.DataFrame(self._products),
            "orders": pd.DataFrame(self._orders),
            "invoices": pd.DataFrame(self._invoices),
            "payments": pd.DataFrame(self._payments),
            "refunds": pd.DataFrame(self._refunds),
        }

    def write_all(self) -> dict[str, Path]:
        datasets = self.generate_all()

        output_dir = Path(self.config.output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)

        paths: dict[str, Path] = {}

        for name, dataframe in datasets.items():
            path = output_dir / f"{name}.csv"
            dataframe.to_csv(path, index=False)
            paths[name] = path

        return paths

