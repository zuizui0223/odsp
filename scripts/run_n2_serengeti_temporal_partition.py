#!/usr/bin/env python3
"""Run the frozen N2 Snapshot Serengeti temporal-partition endpoint."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, datetime, timedelta
import hashlib
import json
from pathlib import Path
import re
from typing import Iterable

import numpy as np

from odsp.temporal_partition import (
    classify_temporal_partition_result,
    score_identity_temporal_transferability,
    temporal_partition_profile,
)


EXPECTED_CONSENSUS_MD5 = "5ed2d32fd09127c178cf9dca8ccfd623"
EXPECTED_EFFORT_MD5 = "27cb42f3feaa0642b17cbde24ba15fbd"
CERTAINTY_MIN = 0.8
INDEPENDENCE_MINUTES = 30
MIN_EVENTS = 500
MIN_SITES = 20
MIN_EVENTS_EACH_FOLD = 50
N_FOLDS = 3
N_PERMUTATIONS = 199
PERMUTATION_SEED = 20260903
ALPHA = 0.05
PSEUDOCOUNT = 0.5
EXCLUDED_GROUPS = {
    "human",
    "birdother",
    "otherbird",
    "reptiles",
    "reptile",
    "rodents",
    "rodent",
}


def _md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())


def _column_map(fieldnames: Iterable[str] | None) -> dict[str, str]:
    if not fieldnames:
        return {}
    return {_norm(name): name for name in fieldnames}


def _get(row: dict[str, str], columns: dict[str, str], *names: str) -> str:
    for name in names:
        key = columns.get(_norm(name))
        if key is not None:
            return str(row.get(key, "")).strip()
    return ""


def _float(value: str) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if np.isfinite(result) else None


def _parse_date(value: str) -> date | None:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d-%b-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def _parse_datetime(value: str) -> datetime | None:
    value = value.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%m/%d/%Y %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _merge_intervals(intervals: list[tuple[date, date]]) -> list[tuple[date, date]]:
    if not intervals:
        return []
    ordered = sorted((min(a, b), max(a, b)) for a, b in intervals)
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end + timedelta(days=1):
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))
    return merged


def _load_effort(path: Path) -> tuple[dict[str, int], dict[str, object]]:
    intervals: dict[str, list[tuple[date, date]]] = defaultdict(list)
    rows = 0
    invalid = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = _column_map(reader.fieldnames)
        for row in reader:
            rows += 1
            site = _get(row, columns, "SiteID", "Site ID", "site")
            start = _parse_date(_get(row, columns, "Start date", "start_date", "start"))
            end = _parse_date(_get(row, columns, "End date", "end_date", "end"))
            if not site or start is None or end is None:
                invalid += 1
                continue
            intervals[site].append((start, end))

    active_days: dict[str, int] = {}
    merged_counts: dict[str, int] = {}
    for site, raw in intervals.items():
        merged = _merge_intervals(raw)
        days = sum((end - start).days + 1 for start, end in merged)
        if days > 0:
            active_days[site] = int(days)
            merged_counts[site] = len(merged)
    return active_days, {
        "rows": rows,
        "invalid_rows": invalid,
        "sites_with_positive_effort": len(active_days),
        "merged_interval_count": int(sum(merged_counts.values())),
        "camera_days": int(sum(active_days.values())),
    }


def _site_fold(site: str) -> int:
    return int(hashlib.sha256(site.encode("utf-8")).hexdigest(), 16) % N_FOLDS


def _load_events(path: Path, active_days: dict[str, int]) -> tuple[list[tuple[str, str, datetime]], dict[str, object]]:
    candidates: list[tuple[str, str, datetime]] = []
    rows = 0
    excluded_uncertain = 0
    excluded_group = 0
    excluded_missing = 0
    excluded_no_effort = 0

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = _column_map(reader.fieldnames)
        required = ["datetime", "siteid", "species", "numvotes", "numclassifications"]
        missing_required = [name for name in required if _norm(name) not in columns]
        if missing_required:
            raise ValueError(f"consensus schema missing required fields: {missing_required}")

        for row in reader:
            rows += 1
            site = _get(row, columns, "SiteID")
            species = _get(row, columns, "Species")
            observed = _parse_datetime(_get(row, columns, "DateTime"))
            votes = _float(_get(row, columns, "NumVotes"))
            classifications = _float(_get(row, columns, "NumClassifications"))
            if not site or not species or observed is None or votes is None or classifications is None or classifications <= 0:
                excluded_missing += 1
                continue
            if site not in active_days:
                excluded_no_effort += 1
                continue
            if votes / classifications < CERTAINTY_MIN:
                excluded_uncertain += 1
                continue
            if _norm(species) in EXCLUDED_GROUPS:
                excluded_group += 1
                continue
            candidates.append((site, species, observed))

    candidates.sort(key=lambda event: (event[0], event[1], event[2]))
    retained: list[tuple[str, str, datetime]] = []
    last_seen: dict[tuple[str, str], datetime] = {}
    minimum_gap = timedelta(minutes=INDEPENDENCE_MINUTES)
    removed_dependence = 0
    for event in candidates:
        site, species, observed = event
        key = (site, species)
        previous = last_seen.get(key)
        if previous is not None and observed - previous < minimum_gap:
            removed_dependence += 1
            continue
        retained.append(event)
        last_seen[key] = observed

    return retained, {
        "rows": rows,
        "candidate_rows_after_quality_effort_filters": len(candidates),
        "retained_independent_events": len(retained),
        "excluded_uncertain": excluded_uncertain,
        "excluded_group_categories": excluded_group,
        "excluded_missing_or_invalid": excluded_missing,
        "excluded_no_effort": excluded_no_effort,
        "removed_same_species_site_within_30min": removed_dependence,
    }


def _admit_species(events: list[tuple[str, str, datetime]]) -> tuple[list[str], dict[str, object]]:
    counts: Counter[str] = Counter()
    sites: dict[str, set[str]] = defaultdict(set)
    fold_counts: dict[str, Counter[int]] = defaultdict(Counter)
    for site, species, _ in events:
        counts[species] += 1
        sites[species].add(site)
        fold_counts[species][_site_fold(site)] += 1

    admitted = []
    audit = {}
    for species in sorted(counts):
        per_fold = [int(fold_counts[species][fold]) for fold in range(N_FOLDS)]
        passes = (
            counts[species] >= MIN_EVENTS
            and len(sites[species]) >= MIN_SITES
            and min(per_fold) >= MIN_EVENTS_EACH_FOLD
        )
        audit[species] = {
            "events": int(counts[species]),
            "sites": len(sites[species]),
            "events_by_fold": per_fold,
            "admitted": bool(passes),
        }
        if passes:
            admitted.append(species)
    return admitted, audit


def _build_support(
    events: list[tuple[str, str, datetime]],
    admitted_species: list[str],
    active_days: dict[str, int],
) -> tuple[np.ndarray, list[str], list[str], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    species_index = {species: index for index, species in enumerate(admitted_species)}
    filtered = [event for event in events if event[1] in species_index]
    sites = sorted({site for site, _, _ in filtered})
    site_index = {site: index for index, site in enumerate(sites)}

    site_values = np.fromiter((site_index[site] for site, _, _ in filtered), dtype=int)
    identity_values = np.fromiter((species_index[species] for _, species, _ in filtered), dtype=int)
    time_values = np.fromiter((observed.hour // 4 for _, _, observed in filtered), dtype=int)
    weights = np.fromiter((1.0 / active_days[site] for site, _, _ in filtered), dtype=float)

    support = np.zeros((len(sites), len(admitted_species), 6), dtype=float)
    np.add.at(support, (site_values, identity_values, time_values), weights)
    folds = np.asarray([_site_fold(site) for site in sites], dtype=int)
    return support, sites, filtered, site_values, identity_values, time_values, weights, folds


def _permutation_null(
    shape: tuple[int, ...],
    site_values: np.ndarray,
    identity_values: np.ndarray,
    time_values: np.ndarray,
    weights: np.ndarray,
) -> list[float]:
    rng = np.random.default_rng(PERMUTATION_SEED)
    groups = [np.flatnonzero(site_values == site) for site in range(shape[0])]
    null_values: list[float] = []
    for _ in range(N_PERMUTATIONS):
        permuted = identity_values.copy()
        for indices in groups:
            if indices.size > 1:
                permuted[indices] = rng.permutation(identity_values[indices])
        support = np.zeros(shape, dtype=float)
        np.add.at(support, (site_values, permuted, time_values), weights)
        profile = temporal_partition_profile(
            support,
            context_axes=(0,),
            identity_axis=1,
            time_axis=2,
        )
        null_values.append(profile.identity_time_partition_information_nats)
    return null_values


def _heldout_gains(support: np.ndarray, site_folds: np.ndarray) -> list[float]:
    gains: list[float] = []
    for fold in range(N_FOLDS):
        model = support[site_folds != fold].sum(axis=0) + PSEUDOCOUNT
        heldout = support[site_folds == fold].sum(axis=0)
        score = score_identity_temporal_transferability(
            model,
            heldout,
            identity_axis=0,
            time_axis=1,
        )
        gains.append(float(score.mean_log_score_gain))
    return gains


def run(consensus: Path, effort: Path) -> dict[str, object]:
    consensus_md5 = _md5(consensus)
    effort_md5 = _md5(effort)
    if consensus_md5 != EXPECTED_CONSENSUS_MD5:
        raise ValueError(f"consensus_data.csv md5 drift: {consensus_md5}")
    if effort_md5 != EXPECTED_EFFORT_MD5:
        raise ValueError(f"search_effort.csv md5 drift: {effort_md5}")

    active_days, effort_audit = _load_effort(effort)
    events, event_audit = _load_events(consensus, active_days)
    admitted, species_audit = _admit_species(events)

    base = {
        "lane_id": "n2_serengeti_temporal_partition_v1",
        "source": {
            "consensus_md5": consensus_md5,
            "effort_md5": effort_md5,
            "timezone": "UTC+03:00_source_local_clock_no_dst",
        },
        "effort_audit": effort_audit,
        "event_audit": event_audit,
        "species_admission_audit": species_audit,
        "admitted_species": admitted,
        "frozen_rules": {
            "certainty_min": CERTAINTY_MIN,
            "independence_minutes": INDEPENDENCE_MINUTES,
            "time_bins_hours": [[0, 4], [4, 8], [8, 12], [12, 16], [16, 20], [20, 24]],
            "site_fold": "sha256_siteid_mod_3",
            "min_events": MIN_EVENTS,
            "min_sites": MIN_SITES,
            "min_events_each_fold": MIN_EVENTS_EACH_FOLD,
            "permutations": N_PERMUTATIONS,
            "permutation_seed": PERMUTATION_SEED,
            "alpha": ALPHA,
            "model_species_time_pseudocount": PSEUDOCOUNT,
        },
    }

    if len(admitted) < 2:
        return {
            **base,
            "terminal_category": "empirical_temporal_partition_unavailable",
            "unavailable_reason": "fewer_than_two_species_passed_frozen_structural_admission",
            "outcome_opened": false,
        }

    support, sites, filtered, site_values, identity_values, time_values, weights, folds = _build_support(
        events,
        admitted,
        active_days,
    )
    profile = temporal_partition_profile(
        support,
        context_axes=(0,),
        identity_axis=1,
        time_axis=2,
    )
    null_values = _permutation_null(
        support.shape,
        site_values,
        identity_values,
        time_values,
        weights,
    )
    gains = _heldout_gains(support, folds)
    decision = classify_temporal_partition_result(
        profile.identity_time_partition_information_nats,
        null_values,
        gains,
        alpha=ALPHA,
    )

    return {
        **base,
        "outcome_opened": true,
        "support_shape_site_species_time": list(map(int, support.shape)),
        "admitted_site_count": len(sites),
        "admitted_event_count": len(filtered),
        "temporal_profile": profile.as_dict(),
        "permutation_null": {
            "draws": len(null_values),
            "mean_nats": float(np.mean(null_values)),
            "q50_nats": float(np.quantile(null_values, 0.50)),
            "q95_nats": float(np.quantile(null_values, 0.95)),
            "max_nats": float(np.max(null_values)),
        },
        "heldout_site_fold_gains": gains,
        "decision": decision.as_dict(),
        "terminal_category": decision.terminal_category,
        "claim_boundary": {
            "measured_object": "camera-detected species-time partition under source clock time and declared effort weighting",
            "true_activity_niche_partition_identified": false,
            "interspecific_displacement_causality_identified": false,
            "solar_time_partition_identified": false,
            "bat_endpoint_reinterpreted": false,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--consensus", type=Path, required=True)
    parser.add_argument("--effort", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = run(args.consensus, args.effort)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "terminal_category": result["terminal_category"],
        "admitted_species": len(result.get("admitted_species", [])),
        "output": str(args.output),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
