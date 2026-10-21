#!/usr/bin/env python3
"""Post-outcome, ALTITUDE-BLIND stork micro-route recurrence diagnostic.

Tracks opportunity for revisiting the same 5km horizontal subcell INSIDE an
already eligible 50km migration corridor cell. Fixed source data, cohort
inclusion, year, and movement filters are inherited from the original
outcome-blind stork stage. Altitude is not read, missingness is not checked,
and the original altitude results are neither re-run nor re-selected.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import statistics
import zipfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from pyproj import Transformer
from . import stork_2014_xytime_source_screen as base

SOURCE = {
    "rotics2013": {
        "doi": "10.5441/001/1.hn1bd23k",
        "year": 2013,
        "gps_zip": "Fall migrations of juvenile vs. adult white storks (data from Rotics et al. 2016)-gps.csv.zip",
        "gps_md5": "2ec22217c0f566650d245ae2da4694bf",
        "reference": "Fall migrations of juvenile vs. adult white storks (data from Rotics et al. 2016)-reference-data.csv",
        "reference_md5": "b38407ed744cf2bd4806afce929f604a",
        "expected_5min": 147773,
        "expected_birds": 25, "expected_days": 111, "expected_fixes": 6951,
        "id_sha256": "901b92d50bfeb763feed6abcdd0b59e27a69b2b0825149b1343769ea2edb69df",
    },
    "flack2014": {
        "doi": "10.5441/001/1.bj96m274",
        "year": 2014,
        "gps_zip": "Fall migration of white storks in 2014-gps.csv.zip",
        "gps_md5": "c1fa0c4ca28d3fce5d61caaac36e87d2",
        "reference": "Fall migration of white storks in 2014-reference-data.csv",
        "reference_md5": "116a3d82cd11e1bb4e16b32532725359",
        "expected_5min": 58971,
        "expected_birds": 11, "expected_days": 33, "expected_fixes": 2040,
        "id_sha256": "a741d2e1bc13d91a49f30ddb2cd13af97db855fd8be3d6c407b75ce827d1ec7d",
    },
}
PROJ = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)
COARSE = 50000
FINE = 5000


def checked_md5(path, expected_name, expected_md5):
    h = hashlib.md5()
    with path.open("rb") as f:
        for piece in iter(lambda: f.read(1 << 20), b""):
            h.update(piece)
    if path.name != expected_name or h.hexdigest() != expected_md5:
        raise ValueError("Immutable source name or checksum mismatch")
    return h.hexdigest()


def source_rows(source_zip):
    z = zipfile.ZipFile(source_zip)
    names = [n for n in z.namelist()
             if n.lower().endswith(".csv")
             and not n.startswith("__MACOSX")
             and not n.rsplit("/", 1)[-1].startswith("._")]
    if len(names) != 1:
        z.close()
        raise ValueError("Expected one real archived CSV")
    raw = z.open(names[0])
    return z, io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")


def load_thinned_xy(reader, year):
    """Access ONLY identity/time/x/y/ground-speed/source-QA columns."""
    first = {}
    counts = Counter()
    for r in reader:
        counts["raw_gps_rows"] += 1
        bird = (r.get("individual-local-identifier") or "").strip()
        if not bird:
            continue
        timestamp = (r.get("timestamp") or "").strip()
        try:
            yr, month = int(timestamp[:4]), int(timestamp[5:7])
            hour, minute = int(timestamp[11:13]), int(timestamp[14:16])
        except (ValueError, TypeError):
            continue
        if yr != year or month not in (8, 9, 10, 11):
            continue
        if not (0 <= hour < 24 and 0 <= minute < 60):
            continue
        if (r.get("visible") or "").lower().strip() == "false":
            continue
        if any((r.get(flag) or "").lower().strip() in {"true", "1", "yes"}
               for flag in ("import-marked-outlier", "manually-marked-outlier")):
            continue
        try:
            lon = float(r["location-long"])
            lat = float(r["location-lat"])
            speed = float(r["ground-speed"])
        except (ValueError, TypeError, KeyError):
            continue
        if not all(math.isfinite(v) for v in (lon, lat, speed)):
            continue
        if not (-180 <= lon <= 180 and -86 <= lat <= 86 and 5 <= speed <= 55):
            continue
        key = (bird, timestamp[:10], hour*12 + minute//5)
        if key not in first or timestamp < first[key][0]:
            first[key] = (timestamp, lon, lat)
        counts["raw_flight_speed_rows"] += 1
    counts["selected_flight_5min_fixes"] = len(first)
    return first, dict(counts)


def make_counter(first):
    fine = Counter()
    for (bird, day, five_bin), (_, lon, lat) in first.items():
        x, y = PROJ.transform(lon, lat)
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError("Previously valid projected coordinates are nonfinite")
        coarse = (math.floor(x/COARSE), math.floor(y/COARSE))
        nested = (math.floor(x/FINE), math.floor(y/FINE))
        fine[bird, day, coarse, nested] += 1
    return fine


def geometry(finecounts):
    """Replicate EXACT original 50km source roster; score only x/y recurrence."""
    coarse_count = Counter()
    bird_fine = Counter()
    date_fine = Counter()
    all_fine = Counter()
    bird_coarse_dates = defaultdict(set)
    birds_by_coarse = defaultdict(set)
    for (bird, day, c, f), n in finecounts.items():
        coarse_count[bird, day, c] += n
        bird_fine[bird, c, f] += n
        date_fine[day, c, f] += n
        all_fine[c, f] += n
        bird_coarse_dates[bird, c].add(day)
        birds_by_coarse[c].add(bird)

    historical = base.eligible_support(coarse_count)
    own_coarse = Counter()
    total_coarse = Counter()
    day_coarse = Counter()
    for (bird, day, c), n in coarse_count.items():
        own_coarse[bird, c] += n
        total_coarse[c] += n
        day_coarse[day, c] += n

    qualified_cell = set()
    day_events = Counter()
    for (bird, day, c), n in coarse_count.items():
        own_other = own_coarse[bird, c] - n
        other_otherdate = total_coarse[c] - own_coarse[bird, c] - day_coarse[day, c] + n
        if own_other >= 10 and other_otherdate >= 10:
            qualified_cell.add((bird, day, c))
            day_events[bird, day] += n

    days_by_bird = Counter()
    for (bird, day), n in day_events.items():
        if n >= 50:
            days_by_bird[bird] += 1
    accepted = {b for b, n in days_by_bird.items() if n >= 2}
    date_ord = {d: date.fromisoformat(d).toordinal()
                for b, d, c in coarse_count}
    sorted_dates = {k: sorted((date_ord[d], d) for d in v)
                    for k, v in bird_coarse_dates.items()}

    details = defaultdict(Counter)
    # Work at the same exact fix and day level as the height-support receipt.
    for (bird, day, coarse, fine), n in finecounts.items():
        if bird not in accepted or (bird, day, coarse) not in qualified_cell:
            continue
        if day_events[bird, day] < 50:
            continue
        own_other_fine = bird_fine[bird, coarse, fine] - n
        other_otherdate_fine = (
            all_fine[coarse, fine] - bird_fine[bird, coarse, fine]
            - date_fine[day, coarse, fine] + n
        )
        if own_other_fine < 0 or other_otherdate_fine < 0:
            raise AssertionError("Bad exact-date individual fine-scale count algebra")
        # Equal-other-BIRD reference: compare with one uniformly chosen other
        # biological bird, not an inflated pooled union over all other birds.
        eligible_others = [
            other for other in birds_by_coarse[coarse]
            if other != bird and
            own_coarse[other, coarse] - coarse_count[other, day, coarse] > 0
        ]
        if not eligible_others:
            raise AssertionError("Original source reference requires another bird")
        matching_other_birds = sum(
            bird_fine[other, coarse, fine]
            - finecounts[other, day, coarse, fine] > 0
            for other in eligible_others
        )
        equal_other_revisit = matching_other_birds / len(eligible_others)
        key = (bird, day)
        details[key]["target"] += n
        details[key]["equal_other_revisit_fraction_times_fixes"] += n * equal_other_revisit
        if own_other_fine > 0:
            details[key]["self_fine_revisited"] += n
        if other_otherdate_fine > 0:
            details[key]["other_fine_revisited"] += n
        if own_other_fine > 0 and other_otherdate_fine > 0:
            details[key]["both_fine_revisited"] += n

        other_days = sorted_dates[bird, coarse]
        lag = min(abs(ord_day - date_ord[day]) for ord_day, d in other_days
                  if d != day)
        details[key]["own_coarse_revisit_gap_days_times_fixes"] += lag*n
        details[key]["nested_fine_unique"] += 1

    bird_days = defaultdict(list)
    for (bird, day), row in sorted(details.items()):
        total = row["target"]
        if total < 50:
            raise AssertionError("Scored bird day has below 50 evaluated fixes")
        bird_days[bird].append({
            "day": day,
            "fixes": total,
            "self_fine_fraction": row["self_fine_revisited"]/total,
            "other_fine_fraction": row["other_fine_revisited"]/total,
            "other_equal_bird_fine_fraction": (
                row["equal_other_revisit_fraction_times_fixes"]/total
            ),
            "fine_self_minus_equal_bird_other": (
                row["self_fine_revisited"]
                - row["equal_other_revisit_fraction_times_fixes"]
            )/total,
            "both_fine_fraction": row["both_fine_revisited"]/total,
            "fine_self_minus_other": (
                row["self_fine_revisited"]-row["other_fine_revisited"]
            )/total,
            "own_coarse_revisit_gap_days": (
                row["own_coarse_revisit_gap_days_times_fixes"]/total
            ),
            "nested_fine_subcells_per_day": row["nested_fine_unique"],
        })

    birds = {}
    for bird, ds in sorted(bird_days.items()):
        if len(ds) < 2:
            raise AssertionError("Accepted bird fails two-day requirement")
        birds[bird] = {
            "days": len(ds), "scored_fixes": sum(d["fixes"] for d in ds),
            **{k: statistics.mean(d[k] for d in ds) for k in (
                "self_fine_fraction", "other_fine_fraction",
                "other_equal_bird_fine_fraction", "fine_self_minus_equal_bird_other",
                "both_fine_fraction", "fine_self_minus_other",
                "own_coarse_revisit_gap_days", "nested_fine_subcells_per_day"
            )}
        }

    if set(birds) != accepted:
        raise AssertionError("Bird identity set does not match source admission")
    reference_hash = hashlib.sha256("\n".join(sorted(accepted)).encode()).hexdigest()
    if reference_hash != historical["eligible_bird_id_fingerprint_sha256"]:
        raise AssertionError("Original source scanner and fine sampler differ")
    sums = {
        "coarse_support": historical,
        "eligible_roster_hash": reference_hash,
        "birds": birds,
        "bird_day_count": len(details),
        "scored_fixes": sum(row["target"] for row in details.values()),
        "equal_bird_summary":{
            key:{
                "n_birds":len(birds),
                "mean": statistics.mean(d[key] for d in birds.values()) if birds else None,
                "median": statistics.median(d[key] for d in birds.values()) if birds else None,
                "minimum": min(d[key] for d in birds.values()) if birds else None,
                "maximum": max(d[key] for d in birds.values()) if birds else None,
            }
            for key in ("self_fine_fraction", "other_fine_fraction",
                        "other_equal_bird_fine_fraction", "fine_self_minus_equal_bird_other",
                        "both_fine_fraction", "fine_self_minus_other",
                        "own_coarse_revisit_gap_days",
                        "nested_fine_subcells_per_day")
        }
    }
    return sums


def audit(gpszip, reference, source):
    cfg = SOURCE[source]
    checked_md5(gpszip, cfg["gps_zip"], cfg["gps_md5"])
    checked_md5(reference, cfg["reference"], cfg["reference_md5"])
    with reference.open("rt",encoding="utf-8-sig",newline="") as f:
        stages, meta=base.read_reference(csv.DictReader(f))
    zipfile_, reader = source_rows(gpszip)
    try:
        original=csv.DictReader(reader)
        mandatory={"individual-local-identifier","timestamp","location-long",
                   "location-lat","ground-speed"}
        if not mandatory.issubset(set(original.fieldnames or [])):
            raise ValueError("Native movement metadata fields unavailable")
        first,metadata=load_thinned_xy(original,cfg["year"])
    finally:
        reader.close();zipfile_.close()
    if len(first)!=cfg["expected_5min"]:
        raise ValueError("Altitude-blind original first-5-minute cohort count drift")
    result = geometry(make_counter(first))
    if (len(result["birds"])!=cfg["expected_birds"]
        or result["bird_day_count"]!=cfg["expected_days"]
        or result["scored_fixes"]!=cfg["expected_fixes"]
        or result["eligible_roster_hash"]!=cfg["id_sha256"]):
        raise ValueError("Changed original 50km source admission; must not rescue")
    return {
        "analysis":"STORK_FINE_CORRIDOR_RECURRENCE_NO_HEIGHT_V1",
        "source":source,"doi":cfg["doi"],
        "source_year":cfg["year"],
        "source_zip_md5":cfg["gps_md5"],"source_reference_md5":cfg["reference_md5"],
        "stage_reference":meta["stage_counts"],
        "GPS_source_time_xy":metadata,
        "geometry":result,
        "altitude_values_read":False,
        "altitude_missingness_used_for_selection":False,
        "post_outcome_exploratory":True,
        "mechanism_identified":False,
        "ecological_boundary":"Fine-route recurrence in the same 50km migration area is an opportunity proxy, not measured wind/thermal uplift, terrain, food or competition."
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",required=True,choices=sorted(SOURCE))
    p.add_argument("--gps-zip",required=True,type=Path)
    p.add_argument("--reference",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    result=audit(args.gps_zip,args.reference,args.source)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "source":result["source"],
        "n_birds":len(result["geometry"]["birds"]),
        "bird_days":result["geometry"]["bird_day_count"],
        "scored_fixes":result["geometry"]["scored_fixes"],
        "self5_mean":result["geometry"]["equal_bird_summary"]["self_fine_fraction"]["mean"],
        "other5_mean":result["geometry"]["equal_bird_summary"]["other_fine_fraction"]["mean"],
        "equal_other_bird5_mean":result["geometry"]["equal_bird_summary"]["other_equal_bird_fine_fraction"]["mean"],
        "self_minus_equal_bird5_mean":result["geometry"]["equal_bird_summary"]["fine_self_minus_equal_bird_other"]["mean"],
        "self_minus_other5_mean":result["geometry"]["equal_bird_summary"]["fine_self_minus_other"]["mean"],
        "own_cell_revisit_gap_days_mean":result["geometry"]["equal_bird_summary"]["own_coarse_revisit_gap_days"]["mean"],
        "GPS_height_opened":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
