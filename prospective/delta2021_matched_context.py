#!/usr/bin/env python3
"""Exploratory matched-bird flight/low-speed stationary score association.

This program imports previously frozen flight per-bird results, recomputes
only preexisting stationary bird score (not the 999-draw ecological endpoint),
and reports a rank correlation of the shared bird IDs.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

from . import medgull_sensitivity as engine
from .delta2021_stationary_shape import source_panels, verify

FLIGHT_SHA256="5e49a9645c1cc54a920639774097bb7a0607fc546b9156e62cdd0a33ccefccf3"
EXPECTED_STATIONARY=(46,590,51960,0.008155087267786831)
EXPECTED_MATCHED=33
EXPECTED_FLIGHT=(40,899,66811,0.045673926106348135)
SEED=20261020
DRAWS=9999
BOOTSTRAPS=5000


def corrected_rho(x:np.ndarray,y:np.ndarray):
    if len(x)<3 or len(x)!=len(y):
        return None
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        return None
    rx=rankdata(x,method="average");ry=rankdata(y,method="average")
    if float(np.std(rx))<1e-12 or float(np.std(ry))<1e-12:
        return None
    return float(np.corrcoef(rx,ry)[0,1])


def compare_matched(flight,stationary,seed=SEED,draws=DRAWS,bootstrap=BOOTSTRAPS):
    ids=sorted(set(flight)&set(stationary))
    rows=[
       {"animal_id":bird,"flight_gain":float(flight[bird]["gain"]),
        "flight_scored_days":int(flight[bird]["days"]),
        "flight_scored_bins":int(flight[bird]["bins"]),
        "stationary_gain":float(stationary[bird]["gain"]),
        "stationary_scored_days":int(stationary[bird]["days"]),
        "stationary_scored_bins":int(stationary[bird]["bins"])}
       for bird in ids
    ]
    x=np.array([r["flight_gain"] for r in rows],dtype=float)
    y=np.array([r["stationary_gain"] for r in rows],dtype=float)
    rho=corrected_rho(x,y)
    concordance=int(np.count_nonzero((x>0)&(y>0)|(x<0)&(y<0)))
    result={
       "matched_birds":len(rows),"flight_birds_total":len(flight),
       "stationary_birds_total":len(stationary),
       "rho":rho,"sign_concordance":concordance,
       "sign_discordance":int(np.count_nonzero((x>0)&(y<0)|(x<0)&(y>0))),
       "n_zero_sign_cases":int(len(x)-np.count_nonzero(x*y)),
       "flight_positive_in_matched":int(np.count_nonzero(x>0)),
       "stationary_positive_in_matched":int(np.count_nonzero(y>0)),
       "same_bird_effect_scale_warning":"Flight and stationary raw log score gain magnitudes are not directly biologically commensurable.",
       "primary_association_metric":"Spearman rho between paired bird-level uncalibrated log-score gains",
       "permutation_requested":draws,"bootstrap_requested":bootstrap
    }
    if rho is None:
        result.update({"permutation_valid":0,"two_sided_permutation_p":None,
                       "rho_bootstrap_percentile_95":None,"pearson":None})
        return result,rows

    rng=np.random.default_rng(seed)
    permuted=np.array([corrected_rho(x,rng.permutation(y)) for _ in range(draws)])
    if not np.all(np.isfinite(permuted)):raise AssertionError("Unexpected nonfinite association null")
    tail=int(np.count_nonzero(np.abs(permuted)>=abs(rho)-1e-14))
    result.update({
       "permutation_valid":draws,
       "tail_abs_rho_at_least_observed":tail,
       "two_sided_permutation_p":float((tail+1)/(draws+1)),
       "permutation_null_mean_rho":float(np.mean(permuted)),
       "pearson":float(np.corrcoef(x,y)[0,1]) if np.std(x)>0 and np.std(y)>0 else None,
    })
    boot=[]
    n=len(rows)
    for i in range(bootstrap):
        ind=rng.integers(0,n,n)
        val=corrected_rho(x[ind],y[ind])
        if val is not None:boot.append(val)
    result["rho_bootstrap_valid"]=len(boot)
    result["rho_bootstrap_percentile_95"]=[float(v) for v in np.quantile(boot,[.025,.975])] if boot else None

    effort_corr={}
    for key in ("flight_scored_days","stationary_scored_days","flight_scored_bins","stationary_scored_bins"):
        z=np.log1p(np.array([r[key] for r in rows],float))
        effort_corr[key]={
           "flight_gain_rho":corrected_rho(x,z),
           "stationary_gain_rho":corrected_rho(y,z)
        }
    result["effort_associations_descriptive"]=effort_corr
    return result,rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gps",type=Path,required=True)
    p.add_argument("--flight-json",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    flight_payload=a.flight_json.read_bytes()
    if hashlib.sha256(flight_payload).hexdigest()!=FLIGHT_SHA256:
        raise ValueError("Original prospectively frozen flight result SHA256 mismatch")
    flight_result=json.loads(flight_payload)
    flight=flight_result["panels"]["Larus fuscus"]["comparisons"]["D1_balanced"]
    if (flight["eligible_birds"],flight["eligible_days"],flight["eligible_bins"])!=EXPECTED_FLIGHT[:3] or abs(flight["mean_gain"]-EXPECTED_FLIGHT[3])>1e-12:
        raise AssertionError("Original flight score changed")

    hashes=verify(a.gps)
    with gzip.open(a.gps,"rt",encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream)
        panels,quality=source_panels(reader)
    x=engine.pack(panels["Larus fuscus"])
    support=engine.support(x,1)
    stat=engine.evaluate(x,1,"balanced")
    if not np.array_equal(stat["day_scored_bins"],support["day_scored_bins"]):
        raise AssertionError("Stationary scorer support mismatches its own preflight")
    if (stat["eligible_birds"],stat["eligible_days"],stat["eligible_bins"])!=EXPECTED_STATIONARY[:3] or abs(stat["mean_gain"]-EXPECTED_STATIONARY[3])>1e-12:
        raise AssertionError("Frozen stationary observation not reproduced")

    comparison,paired=compare_matched(flight["per_bird"],stat["per_bird"])
    if comparison["matched_birds"]!=EXPECTED_MATCHED:
        raise AssertionError("Pre-observed paired-bird intersection changed")
    out={
        "source_doi":"10.5281/zenodo.22102508",
        "source_gps_sha256":hashes["sha256"],
        "original_flight_result_sha256":FLIGHT_SHA256,
        "original_flight_run":39375585874,
        "original_stationary_run":39380619623,
        "estimated_stationary_score_reproduced":True,
        "kernel_sha256":hashlib.sha256(Path(engine.__file__).read_bytes()).hexdigest(),
        "status":"POST_OUTCOME_EXPLORATORY_MATCHED_CONTEXT",
        "not_independent_biological_replication":True,
        "comparison":comparison,
        "caveats":[
          "Bird and tag identity are one-to-one in 2021 and cannot be separated.",
          "Study-specific habitat/perch structure, effort, spatial grain and tag error remain correlated with identity.",
          "Positive cross-context association cannot establish that measurement error causes either original effect.",
          "Null cross-context association cannot establish instrument independence; flight-dependent errors are possible.",
          "Same-bird gain uses two different ecological contexts and references, so magnitude differences do not estimate flight-specific strategy magnitude."
        ],
    }
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/"MATCHED_CONTEXT_RESULT_V1.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    with (a.output/"paired_bird_scores.csv").open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(paired[0]))
        writer.writeheader();writer.writerows(paired)
    print(json.dumps({"matched_birds":comparison["matched_birds"],"rho":comparison["rho"],
       "p":comparison["two_sided_permutation_p"],
       "CI":comparison["rho_bootstrap_percentile_95"],
       "concordance":comparison["sign_concordance"],
       "flight_positive":comparison["flight_positive_in_matched"],
       "stationary_positive":comparison["stationary_positive_in_matched"]},sort_keys=True))


if __name__=="__main__":
    main()
