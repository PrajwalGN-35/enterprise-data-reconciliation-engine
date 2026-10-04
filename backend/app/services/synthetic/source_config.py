"""Configuration for NovaRetail source-system simulations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceSystemConfig:
    """Defines the enterprise source systems used in reconciliation."""

    crm_name: str = "NovaRetail CRM"
    erp_name: str = "NovaRetail ERP"
    payment_name: str = "NovaRetail Payment System"

    crm_output_directory: str = "data/enterprise/sources/crm"
    erp_output_directory: str = "data/enterprise/sources/erp"
    payment_output_directory: str = "data/enterprise/sources/payment"

    crm_customer_id_prefix: str = "CRM-CUST"
    erp_customer_id_prefix: str = "ERP-CUST"
    erp_order_id_prefix: str = "ERP-ORD"
    erp_invoice_id_prefix: str = "ERP-INV"
    payment_id_prefix: str = "PAY-TXN"
