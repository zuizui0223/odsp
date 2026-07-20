"""Adapters from frozen ACSP benchmark outputs into ODSP benchmark units.

This module does not import ACSP or regenerate environmental support. It converts
training-only fold exports produced by ACSP's frozen benchmark protocol into the
explicit ODSP benchmark contract. Held-out coordinates remain evaluation-only.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from .benchmark import BenchmarkUnit


REQUIRED_MANIFEST_COLUMNS = {
    "cohort", "pair_id", "status", "taxon_group", "region_name",
    "west", "south", "east", "north", "species_key", "scientific_name",
}


@dataclass(frozen=True)
class ACSPExportLayout:
    """File naming contract for one frozen ACSP cohort export."""

    root: Path
    cohort: str

    def pair_candidates(self, pair_id: int) -> Path:
        return self.root / f"pair_{int(pair_id):03d}_candidates.csv"

    def pair_folds(self, pair_id: int) -> Path:
        return self.root / f"pair_{int(pair_id):03d}_folds.csv"


def load_frozen_manifest(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = REQUIRED_MANIFEST_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"manifest is missing columns: {', '.join(sorted(missing))}")
    frame = frame[frame["status"].astype(str).eq("predeclared")].copy()
    frame["pair_id"] = pd.to_numeric(frame["pair_id"], errors="raise").astype(int)
    if frame.duplicated(["cohort", "pair_id"]).any():
        raise ValueError("manifest contains duplicate cohort/pair_id rows")
    return frame.reset_index(drop=True)


def _read_nonempty(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _fold_values(frame: pd.DataFrame) -> list[int]:
    for column in ("repeat", "fold", "fold_id"):
        if column in frame.columns:
            values = pd.to_numeric(frame[column], errors="coerce").dropna().astype(int)
            return sorted(values.unique().tolist())
    return []


def units_from_acsp_export(
    manifest: pd.DataFrame,
    layouts: Iterable[ACSPExportLayout],
    *,
    support_col: str = "integrated_support_score",
) -> list[BenchmarkUnit]:
    """Convert ACSP fold exports to ODSP benchmark units.

    Expected candidate exports retain candidate latitude/longitude, a support
    score, and held-out occurrence coordinates or IDs per fold. Exports lacking
    complete training/holdout separation are rejected instead of guessed.
    """
    layout_map = {layout.cohort: layout for layout in layouts}
    units: list[BenchmarkUnit] = []
    for row in manifest.itertuples(index=False):
        if row.cohort not in layout_map:
            continue
        layout = layout_map[row.cohort]
        candidates = _read_nonempty(layout.pair_candidates(row.pair_id))
        folds = _read_nonempty(layout.pair_folds(row.pair_id))
        fold_ids = _fold_values(folds if not folds.empty else candidates)
        if not fold_ids:
            units.append(BenchmarkUnit(
                pair_id=f"{row.cohort}:{row.pair_id}",
                taxon=str(row.scientific_name), region=str(row.region_name),
                fold_id="missing", training_occurrences=pd.DataFrame(),
                candidate_support=pd.DataFrame(), held_out_occurrences=pd.DataFrame(),
                metadata={"source_status": "missing_fold_export"},
            ))
            continue
        for fold_id in fold_ids:
            fold_candidates = candidates[candidates.get("repeat", pd.Series(index=candidates.index, dtype=float)).eq(fold_id)].copy()
            fold_rows = folds[folds.get("repeat", pd.Series(index=folds.index, dtype=float)).eq(fold_id)].copy()
            if support_col not in fold_candidates.columns and "component_local_habitat_score" in fold_candidates.columns:
                fold_candidates[support_col] = fold_candidates["component_local_habitat_score"]
            candidate_cols = [column for column in ("latitude", "longitude", support_col, "site_id") if column in fold_candidates.columns]
            candidate_support = fold_candidates[candidate_cols].copy()
            candidate_support = candidate_support.rename(columns={support_col: "candidate_support"})

            train_lat = next((c for c in ("training_latitude", "train_latitude") if c in fold_rows.columns), None)
            train_lon = next((c for c in ("training_longitude", "train_longitude") if c in fold_rows.columns), None)
            hold_lat = next((c for c in ("heldout_latitude", "held_out_latitude") if c in fold_rows.columns), None)
            hold_lon = next((c for c in ("heldout_longitude", "held_out_longitude") if c in fold_rows.columns), None)
            training = fold_rows[[train_lat, train_lon]].rename(columns={train_lat: "latitude", train_lon: "longitude"}) if train_lat and train_lon else pd.DataFrame()
            held_out = fold_rows[[hold_lat, hold_lon]].rename(columns={hold_lat: "latitude", hold_lon: "longitude"}) if hold_lat and hold_lon else pd.DataFrame()
            units.append(BenchmarkUnit(
                pair_id=f"{row.cohort}:{row.pair_id}",
                taxon=str(row.scientific_name), region=str(row.region_name),
                fold_id=str(fold_id), training_occurrences=training,
                candidate_support=candidate_support, held_out_occurrences=held_out,
                metadata={"cohort": row.cohort, "taxon_group": row.taxon_group,
                          "species_key": int(row.species_key), "source": "acsp_frozen_export"},
            ))
    return units
