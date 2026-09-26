#!/usr/bin/env python3
"""Exploratory Palmer Archipelago island-reassembly analysis.

This script is deliberately separate from the frozen ODSP N2 evidence. It asks an
ecological question: after restricting to Adélie penguins, are island-associated
phenotypes persistent across years or temporally reassembled?
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np

SPECIES_PREFIX = "Adelie"
ISLANDS = ("Biscoe", "Dream", "Torgersen")
YEARS = ("PAL0708", "PAL0809", "PAL0910")
STRUCTURAL = ("Culmen Length (mm)", "Culmen Depth (mm)", "Flipper Length (mm)")
OUTCOMES = (
    "Culmen Length (mm)",
    "Culmen Depth (mm)",
    "Flipper Length (mm)",
    "Body Mass (g)",
    "Delta 15 N (o/oo)",
    "Delta 13 C (o/oo)",
)
ISOTOPES = ("Delta 15 N (o/oo)", "Delta 13 C (o/oo)")


def _finite(value: str) -> bool:
    if value in {"", "NA", "NaN", "nan"}:
        return False
    try:
        return math.isfinite(float(value))
    except ValueError:
        return False


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [row for row in rows if str(row.get("Species", "")).startswith(SPECIES_PREFIX)]


def egg_day(row: dict[str, str]) -> float:
    text = row["Date Egg"]
    month, day = map(int, text[5:10].split("-"))
    return float(day if month == 11 else 30 + day)


def _design(rows: list[dict[str, str]], level: str) -> tuple[np.ndarray, list[str]]:
    names = ["intercept", "male", "year_2008", "year_2009", "egg_day", "clutch_complete"]
    matrix: list[list[float]] = []
    for row in rows:
        y08 = float(row["studyName"] == "PAL0809")
        y09 = float(row["studyName"] == "PAL0910")
        dream = float(row["Island"] == "Dream")
        torg = float(row["Island"] == "Torgersen")
        values = [
            1.0,
            float(row["Sex"] == "MALE"),
            y08,
            y09,
            egg_day(row),
            float(row["Clutch Completion"] == "Yes"),
        ]
        if level in {"island", "reassembly"}:
            values += [dream, torg]
        if level == "reassembly":
            values += [y08 * dream, y08 * torg, y09 * dream, y09 * torg]
        matrix.append(values)
    if level in {"island", "reassembly"}:
        names += ["island_Dream", "island_Torgersen"]
    if level == "reassembly":
        names += ["2008xDream", "2008xTorgersen", "2009xDream", "2009xTorgersen"]
    return np.asarray(matrix, dtype=float), names


def _fit(x: np.ndarray, y: np.ndarray, names: list[str]) -> dict[str, object]:
    beta, _, rank, _ = np.linalg.lstsq(x, y, rcond=None)
    if rank != x.shape[1]:
        raise ValueError("design matrix is rank deficient")
    residual = y - x @ beta
    sse = float(residual @ residual)
    n, p = x.shape
    if not sse > 0:
        raise ValueError("nonpositive SSE")
    aic = n * math.log(sse / n) + 2 * p
    aicc = aic + (2 * p * (p + 1)) / (n - p - 1)
    return {
        "n": n,
        "p": p,
        "sse": sse,
        "aic": aic,
        "aicc": aicc,
        "coefficients": {name: float(value) for name, value in zip(names, beta)},
    }


def outcome_models(rows: list[dict[str, str]], outcome: str) -> dict[str, object]:
    keep = [
        row
        for row in rows
        if row.get("Sex") in {"MALE", "FEMALE"}
        and _finite(row.get(outcome, ""))
        and row.get("Date Egg") not in {"", "NA"}
        and row.get("Clutch Completion") in {"Yes", "No"}
        and row.get("Island") in ISLANDS
        and row.get("studyName") in YEARS
    ]
    y = np.asarray([float(row[outcome]) for row in keep], dtype=float)
    fits: dict[str, dict[str, object]] = {}
    for level in ("baseline", "island", "reassembly"):
        x, names = _design(keep, level)
        fits[level] = _fit(x, y, names)
    baseline = fits["baseline"]
    island = fits["island"]
    reassembly = fits["reassembly"]
    return {
        "n": len(keep),
        "fixed_island_partial_r2": (baseline["sse"] - island["sse"]) / baseline["sse"],
        "fixed_island_delta_aicc": island["aicc"] - baseline["aicc"],
        "island_by_year_partial_r2_given_main": (island["sse"] - reassembly["sse"]) / island["sse"],
        "island_by_year_delta_aicc": reassembly["aicc"] - island["aicc"],
        "fits": fits,
    }


def _equal_sex_cell_mean(rows: list[dict[str, str]], outcome: str, year: str, island: str) -> float | None:
    means = []
    for sex in ("FEMALE", "MALE"):
        vals = [
            float(row[outcome])
            for row in rows
            if row.get("Sex") == sex
            and row.get("studyName") == year
            and row.get("Island") == island
            and _finite(row.get(outcome, ""))
        ]
        if not vals:
            return None
        means.append(float(np.mean(vals)))
    return float(np.mean(means))


def rank_reversals(rows: list[dict[str, str]], outcome: str) -> dict[str, object]:
    means = {
        year: {island: _equal_sex_cell_mean(rows, outcome, year, island) for island in ISLANDS}
        for year in YEARS
    }
    pairs = (("Biscoe", "Dream"), ("Biscoe", "Torgersen"), ("Dream", "Torgersen"))
    reversed_pairs = 0
    details = {}
    for a, b in pairs:
        diffs = [means[year][a] - means[year][b] for year in YEARS]
        signs = {int(np.sign(value)) for value in diffs if value != 0}
        flipped = -1 in signs and 1 in signs
        reversed_pairs += int(flipped)
        details[f"{a}_minus_{b}"] = {"differences": diffs, "sign_reversal": flipped}
    return {
        "equal_sex_cell_means": means,
        "pairwise_contrasts_reversing_sign": reversed_pairs,
        "pair_details": details,
    }


def _nearest_centroid_loyo(rows: list[dict[str, str]], features: tuple[str, ...]) -> dict[str, object]:
    complete = [
        row
        for row in rows
        if row.get("Sex") in {"MALE", "FEMALE"}
        and row.get("Island") in ISLANDS
        and row.get("studyName") in YEARS
        and all(_finite(row.get(feature, "")) for feature in features)
    ]
    folds = []
    for heldout in YEARS:
        train = [row for row in complete if row["studyName"] != heldout]
        test = [row for row in complete if row["studyName"] == heldout]
        sex_means = {
            sex: np.asarray(
                [np.mean([float(r[f]) for r in train if r["Sex"] == sex]) for f in features],
                dtype=float,
            )
            for sex in ("FEMALE", "MALE")
        }

        def residual(row: dict[str, str]) -> np.ndarray:
            return np.asarray([float(row[f]) for f in features], dtype=float) - sex_means[row["Sex"]]

        train_resid = np.vstack([residual(row) for row in train])
        scale = np.std(train_resid, axis=0, ddof=1)
        if np.any(scale <= 0):
            raise ValueError("zero training scale")

        def z(row: dict[str, str]) -> np.ndarray:
            return residual(row) / scale

        centroids = {
            island: np.mean(np.vstack([z(row) for row in train if row["Island"] == island]), axis=0)
            for island in ISLANDS
        }
        correct = {island: 0 for island in ISLANDS}
        counts = {island: 0 for island in ISLANDS}
        for row in test:
            point = z(row)
            pred = min(ISLANDS, key=lambda island: float(np.sum((point - centroids[island]) ** 2)))
            counts[row["Island"]] += 1
            correct[row["Island"]] += int(pred == row["Island"])
        recalls = [correct[island] / counts[island] for island in ISLANDS]
        folds.append(
            {
                "heldout_year": heldout,
                "n": len(test),
                "balanced_accuracy": float(np.mean(recalls)),
                "per_island": {
                    island: {
                        "correct": correct[island],
                        "n": counts[island],
                        "recall": correct[island] / counts[island],
                    }
                    for island in ISLANDS
                },
            }
        )
    return {
        "n_complete": len(complete),
        "features": list(features),
        "chance_balanced_accuracy": 1.0 / len(ISLANDS),
        "folds": folds,
        "mean_balanced_accuracy": float(np.mean([fold["balanced_accuracy"] for fold in folds])),
    }


def analyze(raw_csv: Path) -> dict[str, object]:
    rows = load_rows(raw_csv)
    return {
        "schema_version": 1,
        "analysis_id": "palmer-adelie-island-reassembly-exploratory-v1",
        "status": "exploratory_not_confirmatory",
        "scope": {
            "species": "Pygoscelis adeliae",
            "islands": list(ISLANDS),
            "years": list(YEARS),
            "adelie_rows_raw": len(rows),
        },
        "outcome_models": {outcome: outcome_models(rows, outcome) for outcome in OUTCOMES},
        "rank_reversals": {outcome: rank_reversals(rows, outcome) for outcome in OUTCOMES},
        "cross_year_transfer": {
            "structural_morphology": _nearest_centroid_loyo(rows, STRUCTURAL),
            "isotopic_niche": _nearest_centroid_loyo(rows, ISOTOPES),
        },
        "interpretation_boundary": {
            "no_local_adaptation_claim": True,
            "no_individual_plasticity_claim": True,
            "island_by_year_means_can_reflect_sampling_or_demographic_sorting": True,
            "three_year_window_is_short": True,
            "isotope_signatures_integrate_prebreeding_foraging_not_local_island_foraging": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = analyze(args.raw)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
