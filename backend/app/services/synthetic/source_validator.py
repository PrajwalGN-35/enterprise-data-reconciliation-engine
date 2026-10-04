from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ValidationIssue:
    system: str
    dataset: str
    rule: str
    severity: str
    message: str


class SourceDataValidator:
    """Validate CRM, ERP, and Payment System source datasets."""

    SCHEMAS = {
        ("crm", "customers.csv"): (
            "source_customer_id",
            "master_customer_id",
            "customer_name",
            "email",
            "phone",
            "city",
            "region_id",
            "customer_status",
        ),
        ("erp", "customers.csv"): (
            "source_customer_id",
            "master_customer_id",
            "customer_name",
            "email",
            "phone",
            "city",
            "region_id",
            "customer_status",
        ),
        ("erp", "orders.csv"): (
            "source_order_id",
            "master_order_id",
            "customer_id",
            "product_id",
            "order_date",
            "quantity",
            "total_amount",
            "order_status",
        ),
        ("erp", "invoices.csv"): (
            "source_invoice_id",
            "master_invoice_id",
            "order_id",
            "customer_id",
            "invoice_date",
            "invoice_amount",
            "invoice_status",
        ),
        ("payment", "payments.csv"): (
            "source_payment_id",
            "master_payment_id",
            "invoice_id",
            "customer_id",
            "payment_date",
            "payment_amount",
            "payment_method",
            "payment_status",
        ),
    }

    REQUIRED_COLUMNS = {
        "source_customer_id",
        "master_customer_id",
        "source_order_id",
        "master_order_id",
        "source_invoice_id",
        "master_invoice_id",
        "source_payment_id",
        "master_payment_id",
        "customer_id",
        "product_id",
        "invoice_id",
        "order_id",
        "customer_name",
        "email",
        "payment_status",
        "invoice_amount",
        "payment_amount",
    }

    NUMERIC_COLUMNS = {
        "quantity",
        "total_amount",
        "invoice_amount",
        "payment_amount",
    }

    KEY_COLUMNS = {
        ("crm", "customers.csv"): "source_customer_id",
        ("erp", "customers.csv"): "source_customer_id",
        ("erp", "orders.csv"): "source_order_id",
        ("erp", "invoices.csv"): "source_invoice_id",
        ("payment", "payments.csv"): "source_payment_id",
    }

    def __init__(
        self,
        source_dir: str | Path = Path("data/enterprise/sources"),
    ) -> None:
        self.source_dir = Path(source_dir)

    @staticmethod
    def _add_issue(
        issues: list[ValidationIssue],
        system: str,
        dataset: str,
        rule: str,
        severity: str,
        message: str,
    ) -> None:
        issues.append(
            ValidationIssue(
                system=system,
                dataset=dataset,
                rule=rule,
                severity=severity,
                message=message,
            )
        )

    def _read(
        self,
        system: str,
        dataset: str,
    ) -> pd.DataFrame:
        path = self.source_dir / system / dataset

        if not path.exists():
            raise FileNotFoundError(
                f"Dataset not found: {path}"
            )

        return pd.read_csv(path)

    def validate(self) -> dict[str, Any]:
        issues: list[ValidationIssue] = []
        datasets: dict[tuple[str, str], pd.DataFrame] = {}

        for key, expected_columns in self.SCHEMAS.items():
            system, dataset = key
            dataframe = self._read(system, dataset)
            datasets[key] = dataframe

            missing_columns = [
                column
                for column in expected_columns
                if column not in dataframe.columns
            ]

            unexpected_columns = [
                column
                for column in dataframe.columns
                if column not in expected_columns
            ]

            if missing_columns:
                self._add_issue(
                    issues,
                    system,
                    dataset,
                    "schema",
                    "ERROR",
                    f"Missing columns: {missing_columns}",
                )

            if unexpected_columns:
                self._add_issue(
                    issues,
                    system,
                    dataset,
                    "schema",
                    "WARNING",
                    f"Unexpected columns: {unexpected_columns}",
                )

            if len(dataframe.columns) != len(
                set(dataframe.columns)
            ):
                self._add_issue(
                    issues,
                    system,
                    dataset,
                    "schema",
                    "ERROR",
                    "Duplicate column names detected.",
                )

            for column in dataframe.columns:
                if column in self.REQUIRED_COLUMNS:
                    missing_count = int(
                        dataframe[column].isna().sum()
                    )

                    if missing_count:
                        self._add_issue(
                            issues,
                            system,
                            dataset,
                            "required_field",
                            "ERROR",
                            f"{column} contains "
                            f"{missing_count} missing value(s).",
                        )

                if column in self.NUMERIC_COLUMNS:
                    converted = pd.to_numeric(
                        dataframe[column],
                        errors="coerce",
                    )

                    invalid_mask = (
                        dataframe[column].notna()
                        & converted.isna()
                    )

                    invalid_count = int(
                        invalid_mask.sum()
                    )

                    if invalid_count:
                        self._add_issue(
                            issues,
                            system,
                            dataset,
                            "data_type",
                            "ERROR",
                            f"{column} contains "
                            f"{invalid_count} non-numeric value(s).",
                        )

            key_column = self.KEY_COLUMNS[key]

            if key_column in dataframe.columns:
                duplicate_count = int(
                    dataframe[key_column].duplicated().sum()
                )

                if duplicate_count:
                    self._add_issue(
                        issues,
                        system,
                        dataset,
                        "duplicate_key",
                        "ERROR",
                        f"{key_column} contains "
                        f"{duplicate_count} duplicate record(s).",
                    )

        erp_customers = datasets[
            ("erp", "customers.csv")
        ]
        erp_orders = datasets[
            ("erp", "orders.csv")
        ]
        erp_invoices = datasets[
            ("erp", "invoices.csv")
        ]

        customer_ids = set(
            erp_customers["master_customer_id"].dropna()
        )
        order_ids = set(
            erp_orders["master_order_id"].dropna()
        )

        invalid_customer_refs = ~erp_customers[
            "master_customer_id"
        ].isin(
            set(
                erp_customers[
                    "master_customer_id"
                ].dropna()
            )
        )

        # Customer master IDs are validated against the CRM
        # representation for cross-system consistency.
        crm_customers = datasets[
            ("crm", "customers.csv")
        ]
        crm_master_ids = set(
            crm_customers["master_customer_id"].dropna()
        )

        erp_customer_refs = (
            ~erp_customers["master_customer_id"].isin(
                crm_master_ids
            )
        )

        if erp_customer_refs.any():
            self._add_issue(
                issues,
                "erp",
                "customers.csv",
                "referential_integrity",
                "ERROR",
                f"{int(erp_customer_refs.sum())} ERP "
                "customer record(s) reference unknown "
                "master_customer_id.",
            )

        invalid_invoice_orders = ~erp_invoices[
            "master_invoice_id"
        ].notna()

        # Invoice order references use the source order_id field.
        if "order_id" in erp_invoices.columns:
            invalid_invoice_orders = ~erp_invoices[
                "order_id"
            ].isin(
                set(erp_orders["customer_id"].dropna())
            )

        # The source generator intentionally carries customer_id
        # and order_id as business references; validate existence
        # using the corresponding master relationship where possible.
        if "order_id" in erp_invoices.columns:
            known_source_orders = set(
                erp_orders["master_order_id"].dropna()
            )
            invalid_invoice_orders = ~erp_invoices[
                "order_id"
            ].isin(known_source_orders)

        if invalid_invoice_orders.any():
            self._add_issue(
                issues,
                "erp",
                "invoices.csv",
                "referential_integrity",
                "ERROR",
                f"{int(invalid_invoice_orders.sum())} invoice "
                "record(s) reference unknown order_id.",
            )

        payments = datasets[
            ("payment", "payments.csv")
        ]

        known_invoices = set(
            erp_invoices["master_invoice_id"].dropna()
        )

        invalid_payment_refs = ~payments[
            "invoice_id"
        ].isin(known_invoices)

        if invalid_payment_refs.any():
            self._add_issue(
                issues,
                "payment",
                "payments.csv",
                "referential_integrity",
                "ERROR",
                f"{int(invalid_payment_refs.sum())} payment "
                "record(s) reference unknown invoice_id.",
            )

        for system, dataset, column in (
            (
                "erp",
                "orders.csv",
                "total_amount",
            ),
            (
                "erp",
                "invoices.csv",
                "invoice_amount",
            ),
            (
                "payment",
                "payments.csv",
                "payment_amount",
            ),
        ):
            dataframe = datasets[(system, dataset)]
            numeric = pd.to_numeric(
                dataframe[column],
                errors="coerce",
            )

            negative_count = int((numeric < 0).sum())

            if negative_count:
                self._add_issue(
                    issues,
                    system,
                    dataset,
                    "financial_sanity",
                    "ERROR",
                    f"{column} contains "
                    f"{negative_count} negative value(s).",
                )

        error_count = sum(
            issue.severity == "ERROR"
            for issue in issues
        )

        warning_count = sum(
            issue.severity == "WARNING"
            for issue in issues
        )

        return {
            "valid": error_count == 0,
            "dataset_count": len(datasets),
            "row_counts": {
                f"{system}/{dataset}": int(len(dataframe))
                for (system, dataset), dataframe
                in datasets.items()
            },
            "error_count": error_count,
            "warning_count": warning_count,
            "issues": issues,
        }
