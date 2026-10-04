"""Provide structured access to generated NovaRetail scenario datasets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .scenario_catalog import ScenarioCatalog, ScenarioCatalogEntry


@dataclass(frozen=True)
class DatasetRegistryEntry:
    """Metadata describing one scenario dataset."""

    name: str
    source_system: str
    path: Path
    row_count: int
    columns: tuple[str, ...]


class ScenarioDatasetRegistry:
    """Resolve and load datasets belonging to a cataloged scenario."""

    SOURCE_SYSTEMS = {
        "crm_customers": "crm",
        "erp_customers": "erp",
        "erp_orders": "erp",
        "erp_invoices": "erp",
        "payment_transactions": "payment",
    }

    def __init__(self, scenario: ScenarioCatalogEntry) -> None:
        self.scenario = scenario

    def entries(self) -> list[DatasetRegistryEntry]:
        """Return registry metadata for all datasets in the scenario."""
        manifest = ScenarioCatalog._read_manifest(self.scenario.manifest_path)
        entries: list[DatasetRegistryEntry] = []

        for name, metadata in manifest["datasets"].items():
            path = Path(metadata["path"])

            entries.append(
                DatasetRegistryEntry(
                    name=name,
                    source_system=self.SOURCE_SYSTEMS[name],
                    path=path,
                    row_count=int(metadata["row_count"]),
                    columns=tuple(pd.read_csv(path, nrows=0).columns),
                )
            )

        return entries

    def get(self, name: str) -> DatasetRegistryEntry:
        """Return metadata for one dataset."""
        for entry in self.entries():
            if entry.name == name:
                return entry

        raise KeyError(f"Dataset not found in scenario: {name}")

    def load(self, name: str) -> pd.DataFrame:
        """Load one registered dataset into a DataFrame."""
        entry = self.get(name)

        if not entry.path.exists():
            raise FileNotFoundError(
                f"Registered dataset does not exist: {entry.path}"
            )

        return pd.read_csv(entry.path)

    def load_all(self) -> dict[str, pd.DataFrame]:
        """Load every registered dataset."""
        return {
            entry.name: self.load(entry.name)
            for entry in self.entries()
        }
