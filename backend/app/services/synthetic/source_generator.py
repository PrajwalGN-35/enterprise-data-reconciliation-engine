"""Generate NovaRetail multi-source enterprise datasets."""

from pathlib import Path

import pandas as pd

from .config import SyntheticDataConfig
from .source_config import SourceSystemConfig


class SourceSystemGenerator:
    """Generate CRM, ERP, and Payment System representations."""

    def __init__(
        self,
        config: SyntheticDataConfig | None = None,
        source_config: SourceSystemConfig | None = None,
    ) -> None:
        self.config = config or SyntheticDataConfig()
        self.source_config = source_config or SourceSystemConfig()

    def _master(self) -> dict[str, pd.DataFrame]:
        from .generator import SyntheticEnterpriseGenerator

        generated = SyntheticEnterpriseGenerator(self.config).generate_all()

        if isinstance(generated, dict):
            return generated

        names = [
            "regions",
            "customers",
            "products",
            "orders",
            "invoices",
            "payments",
            "refunds",
        ]

        return dict(zip(names, generated))

    def generate_crm(self, customers: pd.DataFrame) -> pd.DataFrame:
        """Generate the CRM customer representation."""
        records = []

        for _, row in customers.iterrows():
            records.append(
                {
                    "source_customer_id": f"{self.source_config.crm_customer_id_prefix}-{row['customer_id']}",
                    "master_customer_id": row["customer_id"],
                    "customer_name": row["customer_name"],
                    "email": row["email"],
                    "phone": row["phone"],
                    "city": row["city"],
                    "region_id": row["region_id"],
                    "customer_status": row["customer_status"],
                }
            )

        return pd.DataFrame(records)

    def generate_erp(
        self,
        customers: pd.DataFrame,
        orders: pd.DataFrame,
        invoices: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Generate ERP customer, order, and invoice representations."""

        erp_customers = []
        erp_orders = []
        erp_invoices = []

        for _, row in customers.iterrows():
            erp_customers.append(
                {
                    "source_customer_id": f"{self.source_config.erp_customer_id_prefix}-{row['customer_id']}",
                    "master_customer_id": row["customer_id"],
                    "customer_name": row["customer_name"],
                    "email": row["email"],
                    "phone": row["phone"],
                    "city": row["city"],
                    "region_id": row["region_id"],
                    "customer_status": row["customer_status"],
                }
            )

        for _, row in orders.iterrows():
            erp_orders.append(
                {
                    "source_order_id": f"{self.source_config.erp_order_id_prefix}-{row['order_id']}",
                    "master_order_id": row["order_id"],
                    "customer_id": row["customer_id"],
                    "product_id": row["product_id"],
                    "order_date": row["order_date"],
                    "quantity": row["quantity"],
                    "total_amount": row["total_amount"],
                    "order_status": row["order_status"],
                }
            )

        for _, row in invoices.iterrows():
            erp_invoices.append(
                {
                    "source_invoice_id": f"{self.source_config.erp_invoice_id_prefix}-{row['invoice_id']}",
                    "master_invoice_id": row["invoice_id"],
                    "order_id": row["order_id"],
                    "customer_id": row["customer_id"],
                    "invoice_date": row["invoice_date"],
                    "invoice_amount": row["invoice_amount"],
                    "invoice_status": row["invoice_status"],
                }
            )

        return (
            pd.DataFrame(erp_customers),
            pd.DataFrame(erp_orders),
            pd.DataFrame(erp_invoices),
        )

    def generate_payments(self, payments: pd.DataFrame) -> pd.DataFrame:
        """Generate the payment-system representation."""
        records = []

        for _, row in payments.iterrows():
            records.append(
                {
                    "source_payment_id": f"{self.source_config.payment_id_prefix}-{row['payment_id']}",
                    "master_payment_id": row["payment_id"],
                    "invoice_id": row["invoice_id"],
                    "customer_id": row["customer_id"],
                    "payment_date": row["payment_date"],
                    "payment_amount": row["payment_amount"],
                    "payment_method": row["payment_method"],
                    "payment_status": row["payment_status"],
                }
            )

        return pd.DataFrame(records)

    def generate_all_sources(self) -> dict[str, pd.DataFrame]:
        """Generate every source-system dataset."""
        master = self._master()

        crm = self.generate_crm(master["customers"])

        erp_customers, erp_orders, erp_invoices = self.generate_erp(
            master["customers"],
            master["orders"],
            master["invoices"],
        )

        payments = self.generate_payments(master["payments"])

        return {
            "crm_customers": crm,
            "erp_customers": erp_customers,
            "erp_orders": erp_orders,
            "erp_invoices": erp_invoices,
            "payment_transactions": payments,
        }

    def write_all_sources(
        self,
        output_root: str | Path | None = None,
    ) -> dict[str, Path]:
        """Write all source datasets to source-system directories."""
        root = Path(output_root or ".")
        datasets = self.generate_all_sources()

        mapping = {
            "crm_customers": (
                self.source_config.crm_output_directory,
                "customers.csv",
            ),
            "erp_customers": (
                self.source_config.erp_output_directory,
                "customers.csv",
            ),
            "erp_orders": (
                self.source_config.erp_output_directory,
                "orders.csv",
            ),
            "erp_invoices": (
                self.source_config.erp_output_directory,
                "invoices.csv",
            ),
            "payment_transactions": (
                self.source_config.payment_output_directory,
                "payments.csv",
            ),
        }

        paths = {}

        for name, dataframe in datasets.items():
            directory, filename = mapping[name]
            path = root / directory / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            dataframe.to_csv(path, index=False)
            paths[name] = path

        return paths


