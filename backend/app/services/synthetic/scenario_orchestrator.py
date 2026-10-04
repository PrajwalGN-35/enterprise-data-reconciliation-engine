"""Orchestrate deterministic NovaRetail enterprise data scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import SyntheticDataConfig
from .scenario_config import ScenarioConfig, ScenarioType
from .scenario_manifest import ScenarioManifestBuilder
from .source_discrepancy import (
    DiscrepancyInjectionConfig,
    SourceDiscrepancyInjector,
)
from .source_generator import SourceSystemGenerator
from .source_validator import SourceDataValidator


@dataclass(frozen=True)
class ScenarioRunResult:
    """Result produced by an enterprise scenario run."""

    scenario: ScenarioType
    seed: int
    source_root: Path
    dataset_paths: dict[str, Path]
    validation_report: dict[str, Any]
    manifest_path: Path


class EnterpriseScenarioOrchestrator:
    """Generate, optionally corrupt, and validate an enterprise scenario."""

    def __init__(
        self,
        config: ScenarioConfig | None = None,
    ) -> None:
        self.config = config or ScenarioConfig()

    def generate(self) -> ScenarioRunResult:
        """Generate the configured scenario and validate its source data."""

        synthetic_config = SyntheticDataConfig(
            seed=self.config.seed,
        )

        generator = SourceSystemGenerator(
            config=synthetic_config,
        )

        clean_paths = generator.write_all_sources(
            self.config.scenario_root / "clean"
        )

        if self.config.scenario is ScenarioType.CLEAN:
            dataset_paths = clean_paths
            source_root = self.config.clean_source_root

        else:
            injector = SourceDiscrepancyInjector(
                DiscrepancyInjectionConfig(
                    seed=self.config.seed,
                    source_dir=self.config.clean_source_root,
                    output_dir=self.config.discrepant_source_root,
                )
            )

            discrepant_datasets = injector.inject()

            dataset_paths = {
                name: self.config.discrepant_source_root
                / system
                / filename
                for name, (system, filename)
                in SourceDiscrepancyInjector.FILES.items()
            }

            source_root = self.config.discrepant_source_root

            # Keep the generated clean paths available internally so the
            # scenario lifecycle remains deterministic and reproducible.
            _ = discrepant_datasets

        validation_report = SourceDataValidator(
            source_root
        ).validate()

        manifest = ScenarioManifestBuilder().build(
            scenario=self.config.scenario.value,
            seed=self.config.seed,
            source_root=source_root,
            dataset_paths=dataset_paths,
            validation_report=validation_report,
        )

        manifest_path = (
            self.config.scenario_root
            / self.config.scenario.value
            / "scenario_manifest.json"
        )

        ScenarioManifestBuilder().write(
            manifest,
            manifest_path,
        )

        return ScenarioRunResult(
            scenario=self.config.scenario,
            seed=self.config.seed,
            source_root=source_root,
            dataset_paths=dataset_paths,
            validation_report=validation_report,
            manifest_path=manifest_path,
        )
