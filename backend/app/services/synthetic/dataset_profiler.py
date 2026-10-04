"""Profile registered NovaRetail enterprise datasets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .dataset_registry import ScenarioDatasetRegistry


@dataclass(frozen=True)
class ColumnProfile:
    """Profile metadata for one dataset column."""

    name: str
    dtype: str
    row_count: int
    null_count: int
    null_rate: float
    unique_count: int


@dataclass(frozen=True)
class DatasetProfile:
    """Profile metadata for one enterprise dataset."""

    name: str
    source_system: str
    path: Path
    row_count: int
    column_count: int
    columns: tuple[ColumnProfile, ...]


class DatasetProfiler:
    """Generate deterministic structural profiles for registered datasets."""

    def __init__(self, registry: ScenarioDatasetRegistry) -> None:
        self.registry = registry

    def profile(self, name: str) -> DatasetProfile:
        """Profile one registered dataset."""
        entry = self.registry.get(name)
        dataframe = self.registry.load(name)

        row_count = len(dataframe)

        columns = tuple(
            ColumnProfile(
                name=column,
                dtype=str(dataframe[column].dtype),
                row_count=row_count,
                null_count=int(dataframe[column].isna().sum()),
                null_rate=(
                    float(dataframe[column].isna().mean())
                    if row_count
                    else 0.0
                ),
                unique_count=int(dataframe[column].nunique(dropna=True)),
            )
            for column in dataframe.columns
        )

        return DatasetProfile(
            name=entry.name,
            source_system=entry.source_system,
            path=entry.path,
            row_count=row_count,
            column_count=len(dataframe.columns),
            columns=columns,
        )

    def profile_all(self) -> dict[str, DatasetProfile]:
        """Profile every registered dataset."""
        return {
            entry.name: self.profile(entry.name)
            for entry in self.registry.entries()
        }

    @staticmethod
    def to_dict(profile: DatasetProfile) -> dict[str, Any]:
        """Convert a dataset profile into JSON-compatible metadata."""
        return {
            "name": profile.name,
            "source_system": profile.source_system,
            "path": str(profile.path),
            "row_count": profile.row_count,
            "column_count": profile.column_count,
            "columns": [
                {
                    "name": column.name,
                    "dtype": column.dtype,
                    "row_count": column.row_count,
                    "null_count": column.null_count,
                    "null_rate": column.null_rate,
                    "unique_count": column.unique_count,
                }
                for column in profile.columns
            ],
        }
