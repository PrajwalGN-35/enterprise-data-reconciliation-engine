"""Build machine-readable manifests for NovaRetail scenario runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ScenarioManifestBuilder:
    """Create and persist metadata describing a scenario run."""

    def build(
        self,
        *,
        scenario: str,
        seed: int,
        source_root: Path,
        dataset_paths: dict[str, Path],
        validation_report: dict[str, Any],
    ) -> dict[str, Any]:
        """Build a manifest from scenario and validation metadata."""
        row_counts = validation_report.get("row_counts", {})

        datasets = {}
        for name, path in dataset_paths.items():
            datasets[name] = {
                "path": str(path),
                "row_count": int(row_counts.get(name, 0)),
                "exists": path.exists(),
            }

        return {
            "scenario": scenario,
            "seed": seed,
            "source_root": str(source_root),
            "datasets": datasets,
            "validation": {
                "valid": bool(validation_report.get("valid", False)),
                "dataset_count": int(
                    validation_report.get("dataset_count", 0)
                ),
                "error_count": int(
                    validation_report.get("error_count", 0)
                ),
                "warning_count": int(
                    validation_report.get("warning_count", 0)
                ),
            },
        }

    def write(
        self,
        manifest: dict[str, Any],
        path: Path,
    ) -> Path:
        """Write a scenario manifest as formatted JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )
        return path
