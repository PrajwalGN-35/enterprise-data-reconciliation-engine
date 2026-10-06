from dataclasses import fields

from app.services.synthetic.source_config import SourceSystemConfig
from app.services.synthetic.source_models import (
    CRMCustomer,
    ERPCustomer,
    ERPInvoice,
    ERPOrder,
    PaymentTransaction,
)


def test_source_system_configuration_has_three_systems():
    config = SourceSystemConfig()

    assert config.crm_name == "NovaRetail CRM"
    assert config.erp_name == "NovaRetail ERP"
    assert config.payment_name == "NovaRetail Payment System"


def test_source_system_identifiers_are_distinct():
    config = SourceSystemConfig()

    prefixes = {
        config.crm_customer_id_prefix,
        config.erp_customer_id_prefix,
        config.erp_order_id_prefix,
        config.erp_invoice_id_prefix,
        config.payment_id_prefix,
    }

    assert len(prefixes) == 5


def test_crm_customer_model_contains_source_and_master_identity():
    names = {field.name for field in fields(CRMCustomer)}

    assert "source_customer_id" in names
    assert "master_customer_id" in names
    assert "customer_name" in names
    assert "email" in names


def test_erp_models_preserve_master_relationships():
    customer_fields = {field.name for field in fields(ERPCustomer)}
    order_fields = {field.name for field in fields(ERPOrder)}
    invoice_fields = {field.name for field in fields(ERPInvoice)}

    assert "master_customer_id" in customer_fields
    assert "customer_id" in order_fields
    assert "master_order_id" in order_fields
    assert "order_id" in invoice_fields
    assert "master_invoice_id" in invoice_fields


def test_payment_model_links_to_invoice_and_customer():
    names = {field.name for field in fields(PaymentTransaction)}

    assert "invoice_id" in names
    assert "customer_id" in names
    assert "master_payment_id" in names
