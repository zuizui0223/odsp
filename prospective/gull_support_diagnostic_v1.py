"""Decompose existing gull admission failures without inspecting altitude.

Diagnostic only: no frozen scientific endpoint is retuned, rerun, or rescued.
Original Counter-key bug, corrected other-ID support, calendar exclusion, and
short-donor-day filtering are reported separately at the unchanged thresholds.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

from pyproj import Transformer

SOURCES = {
    "medgull2022": ("15685037", "MEDGULL_ANTWERPEN-gps-2022.csv.gz", "aea4ac8900f553e105e797e0553d84e7", 2022, "EPSG:32631", ["Ichthyaetus melanocephalus"]),
    "lbbg2018": ("20706447", "LBBG_SCHIERMONNIKOOG-gps-2018.csv.gz", "e3f8bbc3fdb394824494c1d57b64d399", 2018, "EPSG:32632", ["Larus fuscus"]),
    "delta2020": ("22102508", "DELTATRACK-gps-2020.csv.gz", "730549beb8079213ac893d3bf126c2bf", 2020, "EPSG:32631", ["Larus argentatus", "Larus fuscus"]),
}
STAGES = ("raw_day", "self_other_days", "legacy_bug", "correct_other_ids", "exclude_same_date", "long_donor_days_only")
MIN_DAY, MIN_CELL, MIN_DAYS = 50, 10, 2


def _hash(path: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def stage_counts(counts: dict, stage: str) -> dict:
    """counts keys are (animal ID, UTC date, projected 5-km cell)."""
    if stage not in STAGES:
        raise ValueError(stage)
    raw_days = Counter()
    for (animal, day, cell), n in counts.items():
        if not isinstance(n, int) or n < 0:
            raise ValueError("Counts must be nonnegative integer events")
        raw_days[animal, day] += n
    if stage == "long_donor_days_only":
        counts = {k: n for k, n in counts.items() if raw_days[k[0], k[1]] >= MIN_DAY}
    ac, c, dc = Counter(), Counter(), Counter()
    for (animal, day, cell), n in counts.items():
        ac[animal, cell] += n
        c[cell] += n
        dc[day, cell] += n
    scored = Counter()
    for (animal, day, cell), n in counts.items():
        own = ac[animal, cell] - n
        other = c[cell] - ac[animal, cell]
        different_date_other = c[cell] - ac[animal, cell] - dc[day, cell] + n
        if min(own, other, different_date_other) < 0:
            raise AssertionError("Reference count algebra failed")
        allow = stage == "raw_day"
        if stage in {"self_other_days", "legacy_bug"}:
            allow = own >= MIN_CELL  # Legacy total>=10 is redundant when own>=10.
        elif stage == "correct_other_ids":
            allow = own >= MIN_CELL and other >= MIN_CELL
        elif stage in {"exclude_same_date", "long_donor_days_only"}:
            allow = own >= MIN_CELL and different_date_other >= MIN_CELL
        if allow:
            scored[animal, day] += n
    day_n = Counter(animal for (animal, day), n in scored.items() if n >= MIN_DAY)
    eligible = sorted(animal for animal, n in day_n.items() if n >= MIN_DAYS)
    return {
        "eligible_birds": len(eligible),
        "eligible_days": sum(day_n[a] for a in eligible),
        "scorable_bins_eligible_birds": sum(n for (a, d), n in scored.items() if a in eligible and n >= MIN_DAY),
        "eligible_id_sha256": hashlib.sha256("\n".join(eligible).encode()).hexdigest(),
        "all_scored_days_ge50": sum(n >= MIN_DAY for n in scored.values()),
        "source_birds": len({k[0] for k in counts}),
        "source_bins": sum(counts.values()),
    }


def summarise(counts: dict) -> dict:
    stages = {s: stage_counts(counts, s) for s in STAGES}
    order = ("raw_day", "self_other_days", "correct_other_ids", "exclude_same_date", "long_donor_days_only")
    ns = [stages[s]["eligible_birds"] for s in order]
    if ns != sorted(ns, reverse=True):
        raise AssertionError("Admission funnel must not grow under added restrictions")
    return stages


def load_nonvertical(path: Path, source: str) -> tuple[dict, dict]:
    _, filename, md5, year, epsg, taxa = SOURCES[source]
    if path.name != filename or _hash(path, "md5") != md5:
        raise ValueError("Immutable archive name or checksum mismatch")
    project = Transformer.from_crs("EPSG:4326", epsg, always_xy=True)
    earliest, audit = {}, Counter()
    seen_ids = defaultdict(set)
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = set(reader.fieldnames or [])
        required = {"timestamp", "individual-local-identifier", "individual-taxon-canonical-name", "location-long", "location-lat", "ground-speed"}
        if not required <= fields:
            raise ValueError("Missing nonvertical columns")
        marks = fields & {"import-marked-outlier", "manually-marked-outlier"}
        for r in reader:
            audit["raw_rows"] += 1
            taxon = r["individual-taxon-canonical-name"].strip()
            if taxon not in taxa:
                audit["other_taxon"] += 1
                continue
            a = r["individual-local-identifier"].strip()
            if a:
                seen_ids[taxon].add(a)
            if any(r.get(k, "").strip().lower() in {"true", "t", "1", "yes", "y"} for k in marks):
                audit["provider_outliers"] += 1
                continue
            stamp = r["timestamp"].strip()
            try:
                y, month = int(stamp[:4]), int(stamp[5:7])
                hour, minute = int(stamp[11:13]), int(stamp[14:16])
                lon, lat, speed = float(r["location-long"]), float(r["location-lat"]), float(r["ground-speed"])
            except (ValueError, TypeError):
                audit["invalid_nonvertical_value"] += 1
                continue
            if y != year or month not in {5, 6, 7} or not a:
                continue
            if not (0 <= hour < 24 and 0 <= minute < 60 and -180 <= lon <= 180 and -90 <= lat <= 90 and math.isfinite(speed)):
                continue
            audit["window_xy_speed_rows"] += 1
            if not 5 <= speed <= 55:
                continue
            x, yproj = project.transform(lon, lat)
            if not (math.isfinite(x) and math.isfinite(yproj)):
                continue
            cell = (math.floor(x / 5000), math.floor(yproj / 5000))
            key = (taxon, a, stamp[:10], hour * 12 + minute // 5)
            if key not in earliest or stamp < earliest[key][0]:
                earliest[key] = (stamp, cell)
            audit["flight_proxy_raw_rows"] += 1
    counts = {t: Counter() for t in taxa}
    for (taxon, a, day, bin5), (_, cell) in earliest.items():
        counts[taxon][a, day, cell] += 1
    return counts, {
        "counts": dict(audit), "annual_ids": {t: len(v) for t, v in seen_ids.items()},
        "selected_5min_bins": len(earliest), "md5_verified": md5,
        "input_sha256": _hash(path, "sha256"),
        "height_values_accessed": False, "height_missingness_accessed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=sorted(SOURCES), required=True)
    parser.add_argument("--gps", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    panels, provenance = load_nonvertical(args.gps, args.source)
    result = {
        "diagnostic": "gull-support-root-cause-v1", "source": args.source,
        "provenance": provenance,
        "unchanged_thresholds": {"day_bins": 50, "cell_training": 10, "days_per_bird": 2, "birds_for_primary": 10, "grid_m": 5000, "thin_min": 5},
        "panels": {t: summarise(c) for t, c in panels.items()},
        "ecological_outcome_computed": False,
        "closed_endpoints_changed": False,
        "scope": "Structural diagnostics only; no inference on vertical individuality, no admission rescue.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({t: {s: d["eligible_birds"] for s, d in stages.items()} for t, stages in result["panels"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
