#!/usr/bin/env python3
"""Run the POST-OUTCOME Gyps shared-species Wstar vs bird-specific Wstar audit.

No edits to the published four-panel result, source-roster admission, original
species results, Wstar cutoffs, spatial grain or 10 altitude bins. The new
shared response is evaluated on the same GPS fixes as the bird-specific
reference and its inference remains explicitly exploratory.
"""
from __future__ import annotations

import argparse,csv,hashlib,json
from pathlib import Path

import numpy as np

from . import run_gyps_thermal_50km_height as old
from .gyps_thermal_height_kernel import pack_profiles,permute_day_states,calibrate
from .gyps_species_shared_wstar_kernel import (
    build_shared_context,score_shared_vs_bird
)

N_RANDOMIZATIONS=999
MIN_VALID=950
BIRDS_MIN=10
SEED=20261021
PRIOR_RESULTS={
    "122120597/Gyps fulvus":"supported_50km_thermal_height_shape",
    "352166254/Gyps africanus":"unavailable",
    "44080734/Gyps fulvus":"supported_50km_thermal_height_shape",
    "972560688/Gyps coprotheres":"not_supported_50km_thermal_height_shape"
}


def family_holm(results):
    # This secondary study does not change primary test conclusions.
    names=sorted(results)
    raw={k:results[k].get("calibration",{}).get("p_upper",1.0)
          if results[k]["terminal"]=="exploratory_tested" else 1.0
          for k in names}
    order=sorted(names,key=lambda k:(raw[k],k))
    adjusted=0.0
    for i,key in enumerate(order):
        adjusted=max(adjusted,min(1.0,(len(order)-i)*raw[key]))
        results[key]["exploratory_holm_p_upper"]=adjusted
        results[key]["holm_family_input_p"]=raw[key]
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-extract",type=Path,required=True)
    parser.add_argument("--preheight-result",type=Path,required=True)
    parser.add_argument("--original-primary-result",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    opt=parser.parse_args()
    original=json.loads(opt.original_primary_result.read_text())
    if original["analysis"]!="GYPS_3SPECIES_4STUDIES_50KM_THERMAL_CONTEXT_V1":
        raise ValueError("Original four-study primary study result identity drift")
    if set(original["panels"])!=set(PRIOR_RESULTS):
        raise ValueError("Original source panels were unexpectedly changed")
    for panel,status in PRIOR_RESULTS.items():
        if original["panels"][panel]["terminal"]!=status:
            raise ValueError("Original Gyps ecological evidence categories drifted")
    receipt=json.loads(opt.preheight_result.read_text())
    meta,ids,count=old.original_metadata_source(opt.full_extract)
    frozen=old.validate_preheight(meta,ids,receipt)
    climate=old.wind_states_from_selected(meta,frozen)
    heights,tags,provenance=old.selected_native_height(opt.full_extract,meta)

    panel_results={}
    opt.out.mkdir(parents=True,exist_ok=True)
    for panel in sorted(old.PANEL_SPECS):
        name="/".join(panel)
        sessions,quality=old.make_study_profiles(panel,meta,heights,
             climate.get(panel,{}),tags,provenance)
        result={
            "panel":name,
            "species":panel[1],"source_study_id":panel[0],
            "prior_primary_status":PRIOR_RESULTS[name],
            "preheight_roster_sha256":old.PANEL_SPECS[panel]["sha"],
            "source_height_quality":quality,
            "terminal":"unavailable",
            "exploratory_not_confirmatory":True,
            "source_permutation":N_RANDOMIZATIONS,
            "reason":None
        }
        if sessions is None:
            result["reason"]="original_predeclared_height_quality_unavailable"
            panel_results[name]=result
            continue
        packed=pack_profiles(sessions,climate.get(panel,{}))
        shared=build_shared_context(packed)
        obs=score_shared_vs_bird(packed,shared)
        result["observed"]=obs
        result["shared_response_same_month_other_bird_group_count"]=shared["n_groups"]
        if obs["eligible_birds"]<BIRDS_MIN:
            result["reason"]="not_enough_matched_other_birds_in_both_Wstar_states_same_month_and_50km"
            panel_results[name]=result
            continue
        rng=np.random.default_rng(SEED)
        draws=[]
        for i in range(N_RANDOMIZATIONS):
            perm=permute_day_states(packed,rng)
            value=score_shared_vs_bird(packed,shared,perm)
            if value["eligible_birds"]<BIRDS_MIN:
                value["mean_gain"]=None
            draws.append(dict(draw=i+1,
                mean_gain=value["mean_gain"],
                eligible_birds=value["eligible_birds"],
                eligible_bird_days=value["eligible_bird_days"],
                scored_fixes=value["scored_fixes"]))
            if (i+1)%200==0:
                print("SHARED-WSTAR",name,i+1,flush=True)
        with (opt.out/(
            panel[0]+"_"+panel[1].replace(" ","_")+"_POSTHOC_SHARED_WSTAR_NULL.csv"
        )).open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(draws[0]))
            w.writeheader();w.writerows(draws)
        calibration=calibrate(obs,draws)
        result["calibration"]=calibration
        if calibration["valid"]<MIN_VALID:
            result["reason"]="less_than_950_valid_postoutcome_nulls"
        else:
            result["terminal"]="exploratory_tested"
        panel_results[name]=result

    family_holm(panel_results)
    summary={
       "analysis":"GYPS_SHARED_SPECIES_WSTAR_VS_BIRD_WSTAR_POSTHOC_V1",
       "mode":"post_outcome_noncausal_mechanism_diagnostic",
       "source":"Scacco et al. 2026; 10.5281/zenodo.21915776",
       "source_data_zip_md5":old.ARCHIVE_MD5,
       "frozen_original_primary_run":39594223949,
       "frozen_original_preheight_run":39545718549,
       "original_four_study_test_result_not_modified":True,
       "new_model_contract":"prospective/GYPS_SHARED_VS_INDIVIDUAL_WSTAR_MECHANISM_PLAN_V1.json",
       "primary_wstar_bin_edges_not_modified":True,
       "new_parameter_or_source_grid_optimized_after_outcome":False,
       "randomizations_per_source_requested":N_RANDOMIZATIONS,
       "new_significance_is_exploratory_only":True,
       "panel_results":panel_results
    }
    out=opt.out/"GYPS_SPECIES_SHARED_VS_INDIVIDUAL_WSTAR_POSTHOC_RESULT_V1.json"
    out.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps({key:{
      "status":v["terminal"],"reason":v.get("reason"),
      "birds":v.get("observed",{}).get("eligible_birds"),
      "days":v.get("observed",{}).get("eligible_bird_days"),
      "raw_gain":v.get("observed",{}).get("mean_gain"),
      "null_valid":v.get("calibration",{}).get("valid"),
      "null_excess":v.get("calibration",{}).get("observed_minus_null_mean"),
      "exploratory_holm_upper":v.get("exploratory_holm_p_upper")}
      for key,v in panel_results.items()},sort_keys=True),flush=True)


if __name__=="__main__":
    main()
