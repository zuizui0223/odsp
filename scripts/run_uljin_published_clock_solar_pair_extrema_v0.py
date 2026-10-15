#!/usr/bin/env python3
"""Reanalyze published clock Table 4 vs SOURCE-VERIFIED solar Supplement 2.

Two transformations of SAME year-long detections. Never treat as independent
replication, and never claim the original 41 mirror dates were scored.
"""
import json
import math
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from inspect_uljin_published_supp2_solar_overlap_v0 import analyze, ZIP_URL

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"ULJIN_PUBLISHED_CLOCK_SOLAR_PAIR_EXTREMA_V0_CONTRACT.json"

def compare(plan:dict, authenticated_solar_summary:dict)->dict:
    if (plan.get("schema_version")!=1
        or plan.get("stage")!="POST_PUBLICATION_COMPARISON_TWO_ANALYSES_SAME_EVENTS_NOT_INDEPENDENT_REPLICATION"
        or plan.get("inferential_new_p_values_permitted") is not False
        or plan["uncertainty_claims"]["independent_observation_sets"] is not False
        or plan["uncertainty_claims"]["original_2022_mirror_dates_analyzed"] is not False):
        raise ValueError("HOLD_SOURCE_INFERENCE_SCOPE_MISMATCH")
    if authenticated_solar_summary.get("status")!="SOURCE_VERIFIED_PUBLISHED_SOLAR_TIME_AGGREGATE_ONLY":
        raise ValueError("HOLD_SOLAR_SOURCE_NOT_VERIFIED")
    tabs=authenticated_solar_summary["tables"]
    if len(tabs)!=1 or tabs[0]["status"]!="PUB_AGGREGATE_TABLE":
        raise ValueError("HOLD_NOT_PUBLISHED_SIX_PAIR_TABLE")
    expected={"species_1","species_2","n_1","n_2","estimator","delta","ci_low","ci_high","n_boot","time_basis"}
    if set(tabs[0]["columns"])!=expected or tabs[0]["row_count"]!=6:
        raise ValueError("HOLD_SOLAR_OVERLAP_SCHEMA_NOT_SIX_PAIRS")
    clock={(r["a"],r["b"]):float(r["delta"]) for r in plan["clock_table4_three_decimal"]}
    if len(clock)!=6 or len({*clock})!=6:
        raise ValueError("HOLD_CLOCK_TABLE4_MISSING_PAIRS")
    solar={}
    for r in tabs[0]["rows"]:
        key=(r["species_1"],r["species_2"])
        if key not in clock or key in solar:
            raise ValueError("HOLD_MISMATCH_CLOCK_SOLAR_PAIR_IDENTITIES")
        if r["estimator"]!="Dhat4" or r["time_basis"]!="solar_time" or int(r["n_boot"])!=1000:
            raise ValueError("HOLD_UNEXPECTED_SOLAR_ESTIMATOR")
        delta,lo,hi=map(float,(r["delta"],r["ci_low"],r["ci_high"]))
        if not 0<lo<=delta<=hi<1:
            raise ValueError("HOLD_INVALID_SOLAR_CI")
        solar[key]={"delta":delta,"lo":lo,"hi":hi}
    if len(solar)!=6:
        raise ValueError("HOLD_SIX_SOLAR_PAIRS_REQUIRED")
    clock_low=min(clock,key=clock.get)
    solar_low=min(solar,key=lambda p:solar[p]["delta"])
    clock_high=max(clock,key=clock.get)
    solar_high=max(solar,key=lambda p:solar[p]["delta"])
    return {
       "status":"PUBLISHED_CLOCK_SOLAR_EXTREMA_PERSIST_POSTHOC_NOT_INDEPENDENT",
       "source_doi":plan["article_doi"],
       "solar_doi":plan["solar_supp2_doi"],
       "published_clock_Dhat4_rounded_to_three_decimals":True,
       "solar_source_checksum_verified":True,
       "same_event_population_reused":True,
       "original_41_daylength_pair_effect_computed":False,
       "solar_and_clock_shift_significance_computed":False,
       "all_six_pairs":[{
           "species_a":p[0],"species_b":p[1],
           "published_clock_delta":clock[p],
           "published_solar_delta":round(solar[p]["delta"],9),
           "solar_ci95":[round(solar[p]["lo"],9),round(solar[p]["hi"],9)],
           "solar_minus_rounded_clock":round(solar[p]["delta"]-clock[p],9)
       } for p in clock],
       "lowest_pair_persists":clock_low==solar_low,
       "highest_pair_persists":clock_high==solar_high,
       "lowest_pair":{"species_a":solar_low[0],"species_b":solar_low[1],
         "clock_delta":clock[solar_low],"solar_delta":round(solar[solar_low]["delta"],9)},
       "highest_pair":{"species_a":solar_high[0],"species_b":solar_high[1],
         "clock_delta":clock[solar_high],"solar_delta":round(solar[solar_high]["delta"],9)},
       "independent_replication_claimed":False
    }


def main():
    try:
        req=urllib.request.Request(ZIP_URL,headers={"User-Agent":"ODSP-published-ecology-solar-sensitivity/1.0"})
        with urllib.request.urlopen(req,timeout=35) as res:
            dest=urlparse(res.geturl())
            if dest.scheme!="https" or not (dest.hostname=="zenodo.org" or dest.hostname.endswith(".zenodo.org")):
                raise ValueError("HOLD_UNEXPECTED_ZENODO_REDIRECT")
            data=res.read(1_000_001)
        if len(data)>1_000_000:
            raise ValueError("HOLD_OVERSIZED_SUPPLEMENT")
        out=compare(json.loads(CONTRACT.read_text()),analyze(data))
    except Exception as err:
        out={"status":"HOLD_PUBLISHED_CLOCK_SOLAR_PAIR_EVIDENCE","error_class":type(err).__name__,
             "new_ecological_hypothesis_tested":False}
    print(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2))


if __name__=="__main__":
    main()
