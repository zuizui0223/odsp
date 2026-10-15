#!/usr/bin/env python3
"""Pre-outcome Snapshot Serengeti solstice-mirror site/date feasibility ONLY.

Uses original, md5-pinned search_effort.csv; does not read animal observations.
The source intervals mark the first/last VALID PHOTO on a memory card, not
independently confirmed hourly camera on/off logs. Exact December solstice
calendar mirrors are astronomical PLANNING CANDIDATES, not proven exactly
equal daylight at protected individual camera coordinates.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date, datetime, timedelta
import csv
import hashlib
import json
from pathlib import Path

EFFORT_MD5 = "27cb42f3feaa0642b17cbde24ba15fbd"
MIN_SOLSTICE_DISTANCE_DAYS = 7
MAX_SOLSTICE_DISTANCE_DAYS = 180
MIN_MIRROR_PAIRS = 20


def parse_date(text: str) -> date:
    text = text.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d-%b-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return datetime.fromisoformat(text).date()


def _column_map(fieldnames: list[str] | None) -> dict[str, str]:
    if not fieldnames:
        raise ValueError("EMPTY_SOURCE_HEADER")
    return {"".join(ch for ch in name.lower() if ch.isalnum()): name for name in fieldnames}


def _find(columns: dict[str, str], *names: str) -> str:
    for name in names:
        norm = "".join(ch for ch in name.lower() if ch.isalnum())
        if norm in columns:
            return columns[norm]
    raise ValueError("MISSING_REQUIRED_SOURCE_COLUMN_" + names[0])


def merge_intervals(intervals: list[tuple[date, date]]) -> list[tuple[date, date]]:
    out = []
    for a, b in sorted(intervals):
        if b < a:
            raise ValueError("INVALID_OPERATION_DATES")
        if out and a <= out[-1][1] + timedelta(days=1):
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def _contains(intervals: list[tuple[date,date]], when: date) -> bool:
    return any(a <= when <= b for a,b in intervals)


def mirror_pairs(intervals: list[tuple[date,date]], cycle_year: int) -> list[tuple[date,date]]:
    solstice = date(cycle_year, 12, 21)
    return [
        (solstice - timedelta(days=k), solstice + timedelta(days=k))
        for k in range(MIN_SOLSTICE_DISTANCE_DAYS, MAX_SOLSTICE_DISTANCE_DAYS+1)
        if _contains(intervals, solstice-timedelta(days=k))
        and _contains(intervals, solstice+timedelta(days=k))
    ]


def assess(path: Path) -> dict:
    digest = hashlib.md5(path.read_bytes()).hexdigest()
    if digest != EFFORT_MD5:
        raise ValueError("EFFORT_ORIGINAL_MD5_MISMATCH")
    intervals: dict[str, list[tuple[date,date]]] = defaultdict(list)
    rows=0
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader=csv.DictReader(handle)
        cols=_column_map(reader.fieldnames)
        site_col=_find(cols,"SiteID","Site ID","site")
        start_col=_find(cols,"Start date","start_date","start")
        end_col=_find(cols,"End date","end_date","end")
        for row in reader:
            rows+=1
            site=row[site_col].strip()
            if not site:
                raise ValueError("SOURCE_MISSING_SITE_ID")
            start=parse_date(row[start_col])
            end=parse_date(row[end_col])
            intervals[site].append((start,end))

    merged={site:merge_intervals(values) for site,values in intervals.items()}
    years=sorted({
        y for values in merged.values() for a,b in values
        for y in range(a.year-1,b.year+1)
    })
    summary=[]
    qualifying_sites=set()
    total_site_cycles_with_pairs=0
    summed_pairs=0
    for year in years:
        counts=[len(mirror_pairs(interval,year)) for interval in merged.values()]
        candidate=sum(1 for n in counts if n>0)
        qualifying=sum(1 for n in counts if n>=MIN_MIRROR_PAIRS)
        if candidate==0 and qualifying==0:
            continue
        total_site_cycles_with_pairs+=candidate
        summed_pairs+=sum(counts)
        summary.append({
            "solstice_cycle_year":year,
            "sites_with_at_least_one_calendar_mirror_pair":candidate,
            "sites_with_at_least_20_calendar_mirror_pairs":qualifying,
            "total_site_calendar_mirror_pairs":sum(counts),
        })
    for site, intervals_for_site in merged.items():
        if any(len(mirror_pairs(intervals_for_site,year))>=MIN_MIRROR_PAIRS for year in years):
            qualifying_sites.add(site)

    return {
        "source": "https://zenodo.org/records/5026386/files/search_effort.csv?download=1",
        "source_md5_verified":digest,
        "source_date_interval_rows":rows,
        "distinct_physical_site_ids":len(merged),
        "solstice_cycle_year_aggregates_only":summary,
        "candidate_site_cycles_with_at_least_one_mirror":total_site_cycles_with_pairs,
        "candidate_site_day_pairs":summed_pairs,
        "sites_with_20_plus_calendar_mirrors_any_cycle":len(qualifying_sites),
        "astronomy_scope":"December-21 reflection planning candidates ONLY, not exact site-specific photoperiod matching",
        "camera_operation_scope":"first/last valid SD card photographs, not independently measured physical hour-level on/off",
        "ecological_inference_admitted":False,
        "original_consensus_event_rows_opened":False,
        "seasonal_hysteresis_estimated":False,
        "scientific_status":"HOLD_STATION_HOURLY_OPERATION_Q_AND_NEW_REGION_TRANSFER",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--effort",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    result=assess(args.effort)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "site_count":result["distinct_physical_site_ids"],
        "site_cycles_with_mirrors":result["candidate_site_cycles_with_at_least_one_mirror"],
        "sites_20_plus":result["sites_with_20_plus_calendar_mirrors_any_cycle"],
        "candidate_pairs":result["candidate_site_day_pairs"],
        "original_events_opened":False,
        "status":result["scientific_status"],
    },sort_keys=True))


if __name__ == "__main__":
    main()
