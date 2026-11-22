#!/usr/bin/env python3
"""Gomes v5: explicitly post-outcome detector-q sensitivity curve.

Reuses hash-authenticated original source and already-known v4 original-author
response semantics. This is not a new biological prediction experiment.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
from urllib.request import Request, urlopen

from odsp.detector_partial_identification_v5 import (
    DEFAULT_GAMMAS, curve, gamma_min_for_common_vertical_profile,
    table_from_weighted_cells,
)
from scripts.gomes_zenodo_number_weighted_v4 import (
    SOURCE_SHA256, parse_original,
)
from scripts.gomes_zenodo_vertical_source_preflight_v1 import (
    URL, EXPECTED_MD5,
)

SOURCE_EXPECTED_GAMMA_MIN=78.13449942247023
SOURCE_EXPECTED_TOTAL=16123
SOURCE_EXPECTED_RETAINED=16115
BOOTSTRAP=5000
SEED=20261122

def _quantile(sorted_values, p):
    x=(len(sorted_values)-1)*p
    lower=int(math.floor(x))
    upper=int(math.ceil(x))
    return sorted_values[lower]+(x-lower)*(sorted_values[upper]-sorted_values[lower])

def empirical_sensitivity(cells):
    original_total=Counter()
    days=set()
    for c in cells:
        original_total[c.label]+=c.number
        days.add(c.day)
    if len(days)!=9 or sum(original_total.values())!=SOURCE_EXPECTED_TOTAL:
        raise RuntimeError("original source count roster mismatch")
    keep={s for s, n in original_total.items() if n>5}
    if len(original_total)!=21 or len(keep)!=17:
        raise RuntimeError("original author label eligibility drift")
    originals=table_from_weighted_cells(cells)
    retained=table_from_weighted_cells(cells,eligible_labels=keep)
    if sum(sum(c.values()) for c in retained.values())!=SOURCE_EXPECTED_RETAINED:
        raise RuntimeError("original v4 retained count total changed")

    results=curve(retained,gamma_values=DEFAULT_GAMMAS)
    all_labels_gamma=gamma_min_for_common_vertical_profile(originals)
    if not math.isclose(results["gamma_min_erase_all_label_profiles_plugin"],
                        SOURCE_EXPECTED_GAMMA_MIN,rel_tol=0,abs_tol=1e-8):
        raise RuntimeError("original v4 Gamma_min no longer reproduces")

    by_day=defaultdict(list)
    for c in cells:
        if c.label in keep:
            by_day[c.day].append(c)
    day_names=sorted(days)
    per_day_label_tables={}
    for day in day_names:
        tab=defaultdict(Counter)
        for c in by_day[day]:
            tab[c.label][c.position]+=c.number
        per_day_label_tables[day]=tab
    rng=random.Random(SEED)
    sampled=[]
    for _ in range(BOOTSTRAP):
        names=[rng.choice(day_names) for __ in day_names]
        counts={label: Counter() for label in keep}
        for day in names:
            for label, strata in per_day_label_tables[day].items():
                counts[label].update(strata)
        sampled.append(gamma_min_for_common_vertical_profile(counts))
    sampled.sort()
    results.update({
        "dataset":"Gomes et al. 2020 original Zenodo v1 acoustic calls",
        "dataset_doi":"10.5281/zenodo.4019867",
        "source_sha256":SOURCE_SHA256,
        "original_outcome_opened_prior_to_v5":True,
        "post_outcome_descriptive_only":True,
        "original_bat_acoustic_label_count":len(original_total),
        "retained_author_rule_label_count":len(keep),
        "original_number_sum":sum(original_total.values()),
        "retained_number_sum":SOURCE_EXPECTED_RETAINED,
        "gamma_min_all_original_labels_plugin":all_labels_gamma,
        "source_nights_bootstrap":len(day_names),
        "source_night_bootstrap_replicates":BOOTSTRAP,
        "source_night_bootstrap_gamma_min_2p5_50_97p5_descriptive":[
            _quantile(sampled,.025),_quantile(sampled,.5),_quantile(sampled,.975)
        ],
        "no_independent_sensor_detection_calibration":True,
        "no_site_heldout_validation":True,
    })
    return results


def main():
    req=Request(URL,headers={"User-Agent":"odsp-gomes-postoutcome-gamma-v5/1.0"})
    with urlopen(req,timeout=240) as resp:
        raw=resp.read(4_000_001)
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA256 or hashlib.md5(raw).hexdigest()!=EXPECTED_MD5:
        raise RuntimeError("source hash drift")
    observed=parse_original(raw)
    result=empirical_sensitivity(observed)
    output=Path("results/gomes_detector_identified_set_v5.json")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
