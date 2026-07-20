"""ODSP-native benchmark input contract.

Candidate support is an external, provenance-labelled input. ODSP does not
require ACSP, an SDM, or any particular support-generation algorithm.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import pandas as pd

from .benchmark import BenchmarkUnit


@dataclass
class NativeBenchmarkInput:
    unit: BenchmarkUnit
    training_occurrences: pd.DataFrame
    candidate_support: pd.DataFrame
    held_out_occurrences: pd.DataFrame
    provenance: dict[str, object]


_REQUIRED_LOCATION_COLUMNS = {"latitude", "longitude"}


def _read_locations(path: Path, *, support: bool = False) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = set(_REQUIRED_LOCATION_COLUMNS)
    if support:
        required.add("candidate_support")
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {', '.join(sorted(missing))}")
    return frame


def load_native_benchmark_unit(path: str | Path) -> NativeBenchmarkInput:
    """Load one self-contained ODSP benchmark unit directory.

    Required files:
    - unit.json
    - training_occurrences.csv
    - candidate_support.csv
    - held_out_occurrences.csv
    """
    root = Path(path)
    metadata = json.loads((root / "unit.json").read_text(encoding="utf-8"))
    required_meta = {"taxon", "region", "fold_id", "support_method", "support_frozen_before_holdout"}
    missing = required_meta - set(metadata)
    if missing:
        raise ValueError(f"unit.json is missing keys: {', '.join(sorted(missing))}")
    if metadata["support_frozen_before_holdout"] is not True:
        raise ValueError("candidate support must be frozen before held-out evaluation")
    return NativeBenchmarkInput(
        unit=BenchmarkUnit(str(metadata["taxon"]), str(metadata["region"]), str(metadata["fold_id"])),
        training_occurrences=_read_locations(root / "training_occurrences.csv"),
        candidate_support=_read_locations(root / "candidate_support.csv", support=True),
        held_out_occurrences=_read_locations(root / "held_out_occurrences.csv"),
        provenance=metadata,
    )


def discover_native_benchmark_units(root: str | Path) -> list[Path]:
    """Find ODSP unit directories without assuming a producer-specific layout."""
    base = Path(root)
    return sorted(path.parent for path in base.rglob("unit.json"))
