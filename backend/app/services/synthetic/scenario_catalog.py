"""Catalog generated NovaRetail enterprise scenarios."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScenarioCatalogEntry:
    """Catalog entry for one generated scenario."""

    scenario: str
    seed: int
    manifest_path: Path
    source_root: Path
    valid: bool
    dataset_count: int
    error_count: int
    warning_count: int


class ScenarioCatalog:
    """Discover and index generated scenario manifests."""

    MANIFEST_NAME = "scenario_manifest.json"

    def __init__(self, scenario_root: Path) -> None:
        self.scenario_root = Path(scenario_root)

    def discover(self) -> list[ScenarioCatalogEntry]:
        """Discover all valid scenario manifests under the root."""
        if not self.scenario_root.exists():
            return []

        entries: list[ScenarioCatalogEntry] = []

        for manifest_path in sorted(
            self.scenario_root.rglob(self.MANIFEST_NAME)
        ):
            manifest = self._read_manifest(manifest_path)

            entries.append(
                ScenarioCatalogEntry(
                    scenario=str(manifest["scenario"]),
                    seed=int(manifest["seed"]),
                    manifest_path=manifest_path,
                    source_root=Path(manifest["source_root"]),
                    valid=bool(manifest["validation"]["valid"]),
                    dataset_count=int(
                        manifest["validation"]["dataset_count"]
                    ),
                    error_count=int(
                        manifest["validation"]["error_count"]
                    ),
                    warning_count=int(
                        manifest["validation"]["warning_count"]
                    ),
                )
            )

        return entries

    def get(self, scenario: str) -> ScenarioCatalogEntry | None:
        """Return the first catalog entry matching a scenario."""
        for entry in self.discover():
            if entry.scenario == scenario:
                return entry
        return None

    @staticmethod
    def _read_manifest(path: Path) -> dict[str, Any]:
        """Read and parse a scenario manifest."""
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"Invalid scenario manifest: {path}"
            ) from exc
