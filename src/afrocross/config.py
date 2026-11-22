"""Project-wide paths and analysis parameters.

Keeping parameters in one place makes every analysis choice explicit and easy to
vary in robustness checks (e.g. Top 100 vs Top 200, UK vs US as the target).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"


@dataclass(frozen=True)
class CrossoverConfig:
    """Parameters that define the crossover event. See docs/METHODOLOGY.md."""

    origin_country: str = "NG"
    target_country: str = "GB"
    max_rank: int = 200
    observation_end: str = "2025-12-31"
    min_duration_days: int = 1
