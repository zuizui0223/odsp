"""Adapters from frozen ACSP benchmark outputs into ODSP benchmark inputs.

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
    root: Path
    cohort: str

    def pair_candidates(self, pair_id: int) -> Path:
        return self.root / f"pair_{int(pair_id):03d}_candidates.csv"

    def pair_folds(self, pair_id: int) -> Path:
        return self.root / f"pair_{int(pair_id):03d}_folds.csv"


@dataclass
class AdaptedBenchmarkInput:
    unit: BenchmarkUnit
    training_occurrences: pd.DataFrame
    candidate_support: pd.DataFrame
    held_out_occurrences: pd.DataFrame
    audit: dict[str, object]


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


def _subset_fold(frame: pd.DataFrame, fold_id: int) -> pd.DataFrame:
    for column in ("repeat", "fold", "fold_id"):
        if column in frame.columns:
            return frame[pd.to_numeric(frame[column], errors="coerce").eq(fold_id)].copy()
    return frame.iloc[0:0].copy()


def inputs_from_acsp_export(
    manifest: pd.DataFrame,
    layouts: Iterable[ACSPExportLayout],
    *,
    support_col: str = "integrated_support_score",
) -> list[AdaptedBenchmarkInput]:
    """Convert complete frozen ACSP exports into ODSP benchmark inputs.

    Old exports that contain only coverage IDs but not explicit training and
    held-out coordinates are retained as blocked audit records; coordinates are
    never reconstructed or guessed from IDs.
    """
    layout_map = {layout.cohort: layout for layout in layouts}
    outputs: list[AdaptedBenchmarkInput] = []
    for row in manifest.itertuples(index=False):
        layout = layout_map.get(row.cohort)
        if layout is None:
            continue
        try:
            candidates = _read_nonempty(layout.pair_candidates(row.pair_id))
            folds = _read_nonempty(layout.pair_folds(row.pair_id))
        except FileNotFoundError as exc:
            outputs.append(AdaptedBenchmarkInput(
                BenchmarkUnit(str(row.scientific_name), str(row.region_name), "missing"),
                pd.DataFrame(), pd.DataFrame(), pd.DataFrame(),
                {"status": "missing_export", "path": str(exc), "cohort": row.cohort, "pair_id": int(row.pair_id)},
            ))
            continue

        fold_ids = _fold_values(folds if not folds.empty else candidates)
        if not fold_ids:
            outputs.append(AdaptedBenchmarkInput(
                BenchmarkUnit(str(row.scientific_name), str(row.region_name), "missing"),
                pd.DataFrame(), pd.DataFrame(), pd.DataFrame(),
                {"status": "missing_fold_ids", "cohort": row.cohort, "pair_id": int(row.pair_id)},
            ))
            continue

        for fold_id in fold_ids:
            fold_candidates = _subset_fold(candidates, fold_id)
            fold_rows = _subset_fold(folds, fold_id)
            selected_support = support_col
            if selected_support not in fold_candidates.columns and "component_local_habitat_score" in fold_candidates.columns:
                selected_support = "component_local_habitat_score"
            required_candidate = {"latitude", "longitude", selected_support}
            candidate_missing = required_candidate - set(fold_candidates.columns)

            train_lat = next((c for c in ("training_latitude", "train_latitude") if c in fold_rows.columns), None)
            train_lon = next((c for c in ("training_longitude", "train_longitude") if c in fold_rows.columns), None)
            hold_lat = next((c for c in ("heldout_latitude", "held_out_latitude") if c in fold_rows.columns), None)
            hold_lon = next((c for c in ("heldout_longitude", "held_out_longitude") if c in fold_rows.columns), None)
            coordinate_complete = bool(train_lat and train_lon and hold_lat and hold_lon)

            if candidate_missing or not coordinate_complete:
                status = "blocked_incomplete_legacy_export"
                training = pd.DataFrame()
                held_out = pd.DataFrame()
                candidate_support = pd.DataFrame()
            else:
                status = "ready"
                training = fold_rows[[train_lat, train_lon]].rename(columns={train_lat: "latitude", train_lon: "longitude"}).drop_duplicates()
                held_out = fold_rows[[hold_lat, hold_lon]].rename(columns={hold_lat: "latitude", hold_lon: "longitude"}).drop_duplicates()
                candidate_support = fold_candidates[["latitude", "longitude", selected_support]].rename(columns={selected_support: "candidate_support"})

            outputs.append(AdaptedBenchmarkInput(
                unit=BenchmarkUnit(str(row.scientific_name), str(row.region_name), str(fold_id)),
                training_occurrences=training,
                candidate_support=candidate_support,
                held_out_occurrences=held_out,
                audit={
                    "status": status, "cohort": row.cohort, "pair_id": int(row.pair_id),
                    "taxon_group": row.taxon_group, "species_key": int(row.species_key),
                    "candidate_missing_columns": sorted(candidate_missing),
                    "coordinate_complete": coordinate_complete,
                },
            ))
    return outputs
