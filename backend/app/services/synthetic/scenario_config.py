"""Configuration for NovaRetail enterprise data scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ScenarioType(str, Enum):
    """Supported synthetic enterprise data scenarios."""

    CLEAN = "clean"
    DISCREPANT = "discrepant"


@dataclass(frozen=True)
class ScenarioConfig:
    """Configuration for generating an enterprise data scenario."""

    scenario: ScenarioType = ScenarioType.CLEAN
    seed: int = 20261004
    scenario_root: Path = Path("data/enterprise/scenarios")

    @property
    def clean_source_root(self) -> Path:
        """Return the generated clean source-data directory."""
        return self.scenario_root / "clean" / "data" / "enterprise" / "sources"

    @property
    def discrepant_source_root(self) -> Path:
        """Return the generated discrepant source-data directory."""
        return (
            self.scenario_root
            / "discrepant"
            / "data"
            / "enterprise"
            / "sources_discrepant"
        )

    @property
    def active_source_root(self) -> Path:
        """Return the source directory represented by this scenario."""
        if self.scenario is ScenarioType.DISCREPANT:
            return self.discrepant_source_root

        return self.clean_source_root
