from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class DiscrepancyInjectionConfig:
    """Configuration for deterministic source-data corruption."""

    seed: int = 20261004
    source_dir: Path = Path("data/enterprise/sources")
    output_dir: Path = Path("data/enterprise/sources_discrepant")


class SourceDiscrepancyInjector:
    """Create controlled defective copies of source-system datasets."""

    FILES = {
        "crm_customers": ("crm", "customers.csv"),
        "erp_customers": ("erp", "customers.csv"),
        "erp_orders": ("erp", "orders.csv"),
        "erp_invoices": ("erp", "invoices.csv"),
        "payment_transactions": ("payment", "payments.csv"),
    }

    def __init__(
        self,
        config: DiscrepancyInjectionConfig | None = None,
    ) -> None:
        self.config = config or DiscrepancyInjectionConfig()

    def _read(self, system: str, filename: str) -> pd.DataFrame:
        path = self.config.source_dir / system / filename

        if not path.exists():
            raise FileNotFoundError(
                f"Source dataset not found: {path}"
            )

        return pd.read_csv(path)

    def _write(
        self,
        system: str,
        filename: str,
        dataframe: pd.DataFrame,
    ) -> Path:
        path = self.config.output_dir / system / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        dataframe.to_csv(path, index=False)
        return path

    def inject(self) -> dict[str, pd.DataFrame]:
        """
        Create a deterministic defective copy of every source dataset.

        Defects introduced:
        1. Duplicate CRM customer.
        2. Invalid ERP customer reference.
        3. ERP invoice amount mismatch.
        4. Negative payment amount.
        5. Missing payment status.

        The original source datasets are never modified.
        """

        crm = self._read("crm", "customers.csv")
        erp_customers = self._read("erp", "customers.csv")
        erp_orders = self._read("erp", "orders.csv")
        erp_invoices = self._read("erp", "invoices.csv")
        payments = self._read("payment", "payments.csv")

        required = {
            "crm": crm,
            "erp_customers": erp_customers,
            "erp_orders": erp_orders,
            "erp_invoices": erp_invoices,
            "payments": payments,
        }

        for name, dataframe in required.items():
            if dataframe.empty:
                raise ValueError(
                    f"Required source dataset is empty: {name}"
                )

        # 1. Duplicate CRM customer.
        crm = pd.concat(
            [crm, crm.iloc[[0]].copy()],
            ignore_index=True,
        )

        # 2. Invalid ERP customer reference.
        erp_customers = erp_customers.copy()
        erp_customers.loc[0, "master_customer_id"] = (
            "MASTER-CUST-INVALID"
        )

        # 3. Invoice amount mismatch.
        erp_invoices = erp_invoices.copy()
        amount = pd.to_numeric(
            erp_invoices.loc[0, "invoice_amount"],
            errors="coerce",
        )

        if pd.isna(amount):
            raise ValueError(
                "ERP invoice_amount must be numeric."
            )

        erp_invoices.loc[0, "invoice_amount"] = round(
            float(amount) + 125.00,
            2,
        )

        # 4. Negative payment amount.
        payments = payments.copy()
        payment_amount = pd.to_numeric(
            payments.loc[0, "payment_amount"],
            errors="coerce",
        )

        if pd.isna(payment_amount):
            raise ValueError(
                "Payment amount must be numeric."
            )

        payments.loc[0, "payment_amount"] = -abs(
            float(payment_amount)
        )

        # 5. Missing payment status.
        payments.loc[1, "payment_status"] = pd.NA

        outputs = {
            "crm_customers": crm,
            "erp_customers": erp_customers,
            "erp_orders": erp_orders,
            "erp_invoices": erp_invoices,
            "payment_transactions": payments,
        }

        for name, dataframe in outputs.items():
            system, filename = self.FILES[name]
            self._write(system, filename, dataframe)

        return outputs
