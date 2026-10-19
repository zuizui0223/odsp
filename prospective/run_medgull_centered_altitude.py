#!/usr/bin/env python3
"""Frozen Mediterranean gull 2022 centered flight-altitude identity test.

Run only under MEDGULL_CENTERED_ALTITUDE_TEST_FREEZE_V1.json, after structural
x-y/time support selection. One calendar day is one biological session.
Input may contain altitude, unlike the separately completed pre-outcome screen.
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
import random
import statistics

import numpy as np
from pyproj import Transformer

from prospective.screen_gull_event_support import (
    GRID_METERS, PRIMARY_MONTHS, PRIMARY_SPEED_MS,
    truthy_outlier, utc_day_and_bin,
)

MIN_HEIGHT = -300.0
MAX_HEIGHT = 3000.0
MAX_SPEED = 55.0
MIN_QUALITY_FRACTION = 0.8
MIN_CELL_TRAIN = 10
MIN_DAY_SCORE = 50
MIN_BIRD_DAYS = 2
MIN_BIRDS = 10
BIN_EDGES = np.array([-np.inf, -200, -100, -50, -25, 0, 25, 50, 100, 200, np.inf])
N_BINS = len(BIN_EDGES) - 1
PSEUDOCOUNT = 0.5
EXPECTED_YEAR = 2022
EXPECTED_SOURCE = "medgull"
PERMUTATIONS = 999
MIN_VALID_NULL = 950
SEED = 20261019


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_flight_sessions(path: Path) -> tuple[list[dict], dict]:
    if not path.name.endswith("-gps-2022.csv.gz"):
        raise ValueError("Primary 2022 endpoint must not inspect other year files")
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32631", always_xy=True)
    # ((animal, UTC day, 5min-bin) -> (timestamp, cell, raw altitude string)).
    earliest = {}
    counters = Counter()
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        required = {
            "timestamp", "location-long", "location-lat",
            "ground-speed", "individual-local-identifier", "height-above-msl",
        }
        if not fields.issubset(fields) or not required.issubset(fields):
            raise ValueError("Native fields unavailable; no guessing column aliases")
        outlier_columns = fields & {"manually-marked-outlier", "import-marked-outlier"}
        for row in reader:
            counters["raw_rows"] += 1
            if any(truthy_outlier(row.get(name,"")) for name in outlier_columns):
                counters["source_outliers"] += 1
                continue
            time_state = utc_day_and_bin(row.get("timestamp",""))
            if time_state is None:
                continue
            day, b, month = time_state
            if int(day[:4]) != EXPECTED_YEAR or month not in PRIMARY_MONTHS:
                continue
            animal = (row.get("individual-local-identifier") or "").strip()
            if not animal:
                continue
            try:
                lon, lat = float(row["location-long"]), float(row["location-lat"])
                speed = float(row["ground-speed"])
            except (TypeError, ValueError):
                continue
            if not all(math.isfinite(x) for x in (lon,lat,speed)):
                continue
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                continue
            if not (PRIMARY_SPEED_MS <= speed <= MAX_SPEED):
                continue
            x,y = transformer.transform(lon, lat)
            if not (math.isfinite(x) and math.isfinite(y)):
                continue
            cell = (math.floor(x/GRID_METERS), math.floor(y/GRID_METERS))
            key=(animal, day, b)
            t=(row.get("timestamp") or "").strip()
            if key not in earliest or t < earliest[key][0]:
                earliest[key]=(t, cell, row.get("height-above-msl", ""))

    total_bins = len(earliest)
    retained = defaultdict(list)
    missing = 0
    out_of_range = 0
    for (animal, day, _), (_,cell,raw_height) in earliest.items():
        try:
            height=float(raw_height)
        except (ValueError,TypeError):
            missing += 1
            continue
        if not math.isfinite(height):
            missing += 1
            continue
        if not MIN_HEIGHT <= height <= MAX_HEIGHT:
            out_of_range += 1
            continue
        retained[animal,day].append((cell,height))

    valid_bins=sum(len(events) for events in retained.values())
    sessions=[]
    for (animal,day),events in sorted(retained.items()):
        if len(events) < MIN_DAY_SCORE:
            continue
        median=statistics.median(z for _,z in events)
        hist=defaultdict(lambda: np.zeros(N_BINS, dtype=np.int32))
        for cell,z in events:
            b=int(np.searchsorted(BIN_EDGES,z-median,side="right")-1)
            if not (0 <= b < N_BINS):
                raise AssertionError("Unbinned finite-centered altitude")
            hist[cell][b]+=1
        sessions.append({
            "id":animal, "day":day, "month":int(day[5:7]),
            "hist":dict(hist), "valid":len(events),
        })
    quality={
        "gps_file":path.name,
        "input_gzip_sha256":_digest(path),
        "all_raw_rows":counters["raw_rows"],
        "source_marked_outliers":counters["source_outliers"],
        "flight_proxy_5min_bins":total_bins,
        "flight_5min_altitude_missing":missing,
        "flight_5min_altitude_out_of_frozen_range":out_of_range,
        "valid_altitude_bins":valid_bins,
        "valid_altitude_fraction":valid_bins / total_bins if total_bins else None,
        "days_with_at_least_50_valid_bins":len(sessions),
        "birds_with_at_least_50_valid_bins_on_any_day":len(set(s["id"] for s in sessions)),
        "qc_pass":bool(total_bins and valid_bins/total_bins >= MIN_QUALITY_FRACTION),
        "field":"height-above-msl","field_units":"m", "centered_shape":True,
    }
    return sessions, quality


def _assign_labels(sessions: list[dict], seed: int) -> tuple[list[str], int]:
    """Constrained within-month swaps: preserve identity counts AND unique bird/day."""
    rng=random.Random(seed)
    labels=[s["id"] for s in sessions]
    occupied={(labels[i],s["day"]):i for i,s in enumerate(sessions)}
    if len(occupied) != len(sessions):
        raise AssertionError("source contains more than one original session per bird/day")
    by_month=defaultdict(list)
    for i,s in enumerate(sessions):
        by_month[s["month"]].append(i)
    accepted=0
    for group in by_month.values():
        if len(group)<2:
            continue
        for _ in range(50*len(group)):
            i,j=rng.sample(group,2)
            a,b=labels[i],labels[j]
            if a==b:
                continue
            di,dj=sessions[i]["day"],sessions[j]["day"]
            at=occupied.get((b,di))
            bt=occupied.get((a,dj))
            if (at is not None and at not in {i,j}) or (bt is not None and bt not in {i,j}):
                continue
            del occupied[(a,di)]
            del occupied[(b,dj)]
            labels[i],labels[j]=b,a
            occupied[(b,di)],occupied[(a,dj)]=i,j
            accepted+=1
    return labels,accepted


def score(sessions: list[dict], labels: list[str], min_birds: int = MIN_BIRDS) -> dict:
    assert len(sessions)==len(labels)
    by_id_cell=defaultdict(lambda: np.zeros(N_BINS, dtype=np.int64))
    by_cell=defaultdict(lambda: np.zeros(N_BINS, dtype=np.int64))
    by_day_cell=defaultdict(lambda: np.zeros(N_BINS, dtype=np.int64))
    by_id_day_cell=defaultdict(lambda: np.zeros(N_BINS, dtype=np.int64))
    for s,identity in zip(sessions,labels):
        for cell,n in s["hist"].items():
            by_id_cell[identity,cell] += n
            by_cell[cell] += n
            by_day_cell[s["day"],cell] += n
            by_id_day_cell[identity,s["day"],cell] += n

    bird_day_gains=defaultdict(list)
    scored_fix_total=0
    for s,identity in zip(sessions, labels):
        day=s["day"]
        gain=0.0
        n_test=0
        for cell,targets in s["hist"].items():
            own_other=by_id_cell[identity,cell]-by_id_day_cell[identity,day,cell]
            other_days_others=(by_cell[cell] - by_id_cell[identity,cell]
                               - by_day_cell[day,cell]
                               + by_id_day_cell[identity,day,cell])
            n_own=int(own_other.sum())
            n_other=int(other_days_others.sum())
            if n_own < MIN_CELL_TRAIN or n_other < MIN_CELL_TRAIN:
                continue
            self_probs=(own_other+PSEUDOCOUNT)/(n_own + PSEUDOCOUNT*N_BINS)
            other_probs=(other_days_others+PSEUDOCOUNT)/(n_other + PSEUDOCOUNT*N_BINS)
            gain+=float(np.dot(targets,np.log(self_probs)-np.log(other_probs)))
            n_test+=int(targets.sum())
        if n_test >= MIN_DAY_SCORE:
            bird_day_gains[identity].append(gain/n_test)
            scored_fix_total+=n_test
    bird_scores={
        bird:float(np.mean(scores))
        for bird,scores in bird_day_gains.items()
        if len(scores)>=MIN_BIRD_DAYS
    }
    n=len(bird_scores)
    return {
        "estimable":n>=min_birds,
        "mean_gain":float(np.mean(list(bird_scores.values()))) if n else None,
        "eligible_birds":n,
        "eligible_scored_days":sum(len(bird_day_gains[x]) for x in bird_scores),
        "scored_fixes_total_before_eligible_filter":scored_fix_total,
        "per_bird_scores":bird_scores,
    }


def run(sessions: list[dict], quality: dict, permutations: int=PERMUTATIONS,
        min_birds: int=MIN_BIRDS, min_valid_null: int=MIN_VALID_NULL) -> dict:
    out={
        "endpoint":"medgull-centered-altitude-shape-v1",
        "frozen_contract":"prospective/MEDGULL_CENTERED_ALTITUDE_TEST_FREEZE_V1.json",
        "source_status":"preoutcome_structural_potential_only",
        "quality":quality,
        "fixed": {
            "year":2022,"months":[5,6,7],"speed_range_ms":[5,55],
            "thinning_min":5,"grid_m":5000,"epsg":32631,
            "height_qc_m":[MIN_HEIGHT,MAX_HEIGHT],
            "centered_bins_m":[str(x) for x in BIN_EDGES],
            "smoothing":0.5,
            "permutation_strategy":"whole-day label swaps constrained within calendar month, bird/day uniqueness and bird/month count preserved",
            "null_draws":permutations,"seed":SEED
        },
    }
    if not quality["qc_pass"]:
        out.update({"terminal":"altitude_quality_unavailable", "reason":"frozen 80% height-completeness gate fails"})
        return out
    observed=score(sessions,[s["id"] for s in sessions],min_birds=min_birds)
    out["observed"]={k:v for k,v in observed.items() if k != "per_bird_scores"}
    if not observed["estimable"]:
        out.update({"terminal":"altitude_supported_individuals_unavailable","reason":"under frozen minimum bird+day support after vertical QC"})
        return out
    draws=[]
    null_accepted_swaps=0
    for perm in range(permutations):
        labels,accepted=_assign_labels(sessions,seed=SEED+perm+1)
        null_accepted_swaps+=accepted
        s=score(sessions,labels,min_birds=min_birds)
        if s["estimable"] and s["mean_gain"] is not None:
            draws.append(s["mean_gain"])
    out["null"]={
        "requested":permutations,
        "valid":len(draws),
        "invalid":permutations-len(draws),
        "accepted_swaps_total":null_accepted_swaps,
    }
    if len(draws) < min_valid_null or null_accepted_swaps == 0:
        out.update({"terminal":"null_support_unavailable","reason":"frozen >=950/999 valid null permutations or nontrivial swaps rule fails"})
        return out
    t=observed["mean_gain"]
    nullmean=float(np.mean(draws))
    p=(1+sum(x>=t for x in draws))/(1+len(draws))
    out["null"].update({
        "mean":nullmean,
        "std":float(np.std(draws,ddof=1)),
        "quantiles_025_50_975":np.quantile(draws,[0.025,0.5,0.975]).tolist(),
        "one_sided_p":p,
        "calibrated_excess":t-nullmean,
    })
    out["terminal"]="centered_individual_shape_supported" if t>nullmean and p<0.05 else "centered_individual_shape_not_supported"
    out["limits"]=[
        "Only one nonbat species; cross-taxon generality not established",
        "day median estimated from heldout day itself; shape identity, not real-time absolute-altitude forecasting",
        "GPS tag-specific non-additive error and mixtures of unmeasured behavioural states remain confounds",
        "5-km cell matching is not exact continuous horizontal path matching",
        "one individual rather than one fix is the inferential replication unit",
    ]
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gps",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    ns=p.parse_args()
    sessions,quality=extract_flight_sessions(ns.gps)
    res=run(sessions,quality)
    ns.out.parent.mkdir(parents=True,exist_ok=True)
    ns.out.write_text(json.dumps(res,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    short={
        "terminal":res["terminal"],
        "valid_altitude_fraction":quality["valid_altitude_fraction"],
        "eligible_birds":res.get("observed",{}).get("eligible_birds"),
        "observed_mean_gain":res.get("observed",{}).get("mean_gain"),
        "null_p":res.get("null",{}).get("one_sided_p"),
        "null_valid":res.get("null",{}).get("valid"),
    }
    print(json.dumps(short,sort_keys=True))


if __name__=="__main__":
    main()
