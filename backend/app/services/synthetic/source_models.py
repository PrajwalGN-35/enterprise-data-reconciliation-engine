"""Domain models for NovaRetail source-system representations."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class CRMCustomer:
    """Customer representation owned by the CRM."""

    source_customer_id: str
    master_customer_id: str
    customer_name: str
    email: str
    phone: str
    city: str
    region_id: str
    customer_status: str


@dataclass(frozen=True)
class ERPCustomer:
    """Customer representation owned by the ERP."""

    source_customer_id: str
    master_customer_id: str
    customer_name: str
    email: str
    phone: str
    city: str
    region_id: str
    customer_status: str


@dataclass(frozen=True)
class ERPOrder:
    """Order representation owned by the ERP."""

    source_order_id: str
    master_order_id: str
    customer_id: str
    product_id: str
    order_date: date
    quantity: int
    total_amount: Decimal
    order_status: str


@dataclass(frozen=True)
class ERPInvoice:
    """Invoice representation owned by the ERP."""

    source_invoice_id: str
    master_invoice_id: str
    order_id: str
    customer_id: str
    invoice_date: date
    invoice_amount: Decimal
    invoice_status: str


@dataclass(frozen=True)
class PaymentTransaction:
    """Payment representation owned by the payment system."""

    source_payment_id: str
    master_payment_id: str
    invoice_id: str
    customer_id: str
    payment_date: date
    payment_amount: Decimal
    payment_method: str
    payment_status: str
