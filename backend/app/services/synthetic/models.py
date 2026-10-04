"""Domain models used by the synthetic enterprise data layer."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Region:
    region_id: str
    region_name: str
    country: str


@dataclass(frozen=True)
class Customer:
    customer_id: str
    customer_name: str
    email: str
    phone: str
    region_id: str
    customer_status: str


@dataclass(frozen=True)
class Product:
    product_id: str
    product_name: str
    category: str
    unit_price: Decimal
    product_status: str


@dataclass(frozen=True)
class Order:
    order_id: str
    customer_id: str
    product_id: str
    order_date: date
    quantity: int
    total_amount: Decimal
    order_status: str


@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    order_id: str
    customer_id: str
    invoice_date: date
    invoice_amount: Decimal
    invoice_status: str


@dataclass(frozen=True)
class Payment:
    payment_id: str
    invoice_id: str
    customer_id: str
    payment_date: date
    payment_amount: Decimal
    payment_status: str


@dataclass(frozen=True)
class Refund:
    refund_id: str
    order_id: str
    customer_id: str
    refund_date: date
    refund_amount: Decimal
    refund_status: str

