"""Post-outcome DESCRIPTIVE taxon-standardized contrasts from pinned first v2 receipt.

No source-data reopening; no bootstrap, p-value, fitted model or testing
of a newly selected positive subset. Reads exactly one original pinned
2026-10-08 GitHub Actions first-result JSON file and fails closed on SHA.

The original aggregate is a mean of SITE seasonal averages pooled over taxa.
An arithmetic mean of taxon-site means is a DIFFERENT estimand. Missing
site x taxon x season matching and per-taxon future year counts make
mechanistic decomposition and complete eligibility UNIDENTIFIABLE here.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Any

import numpy as np

METHOD_VERSION="ri_solar_v2_taxon_standardization_postoutcome_v0"


def _nonnegative_int(value:object, name:str)->int:
    if isinstance(value,bool) or not isinstance(value,int) or value<0:
        raise ValueError(f"{name} must be nonnegative integer")
    return value


def _finite(value:object,name:str)->float:
    if isinstance(value,bool) or not isinstance(value,(int,float)):
        raise ValueError(f"{name} must be numeric")
    v=float(value)
    if not math.isfinite(v):
        raise ValueError(f"{name} must be finite")
    return v


def analyze_pinned_taxonomic_receipt(
    raw_original:bytes,
    frozen_plan:Mapping[str,object],
)->dict[str,Any]:
    """Inspect ONLY frozen first-result taxon summaries and original aggregate."""
    if not isinstance(raw_original,bytes):
        raise ValueError("original receipt must be exact bytes")
    if (frozen_plan.get("schema_version")!=1
        or frozen_plan.get("analysis_id")!=
           "ri-solar-v2-postoutcome-taxon-composition-sensitivity-v0"
        or frozen_plan.get("status")!=
           "POST_OUTCOME_DESCRIPTIVE_EXPLORATION_NOT_CONFIRMATORY"
        or frozen_plan.get("no_significance_tests_or_resampled_p_values") is not True
        or frozen_plan.get("never_reclassify_v0_v1_v2_or_any_qualified_route") is not True):
        raise ValueError("unrecognized frozen taxon-standardization plan")
    evidence=frozen_plan.get("input",{})
    digest=hashlib.sha256(raw_original).hexdigest()
    if evidence.get("original_receipt_json_sha256")!=digest:
        raise ValueError("original empirical receipt SHA256 differs from frozen first run")
    if evidence.get("first_frozen_v2_result_run")!=37747931559:
        raise ValueError("original first run identity mismatch")
    data=json.loads(raw_original)
    if (data.get("method_version")!=
            "odsp-ri-solar-vs-clock-yearseason-v2-exploratory"
        or data.get("status")!="EXPLORATORY_NOT_SUPPORTED_OR_UNAVAILABLE"
        or data.get("scored_heldout_events")!=19916):
        raise ValueError("original first empirical scientific status/identity changed")
    original=data.get("primary_heldout_solar_clock")
    taxa=data.get("species_secondary_descriptive")
    if not isinstance(taxa,dict) or not isinstance(original,dict):
        raise ValueError("missing original frozen taxon or site aggregate summaries")
    if len(taxa)==0:
        raise ValueError("original species result empty")
    disallowed=set(frozen_plan["explicit_taxa_nonmammal_or_non_species"])
    floor_sites=_nonnegative_int(
        frozen_plan["minimum_each_season_site_count"],"minimum_each_season_site_count"
    )
    floor_events=_nonnegative_int(
        frozen_plan["minimum_total_taxon_scored_events"],"minimum_total_taxon_scored_events"
    )
    if floor_sites!=8 or floor_events!=100:
        raise ValueError("original declared taxon screening thresholds altered")
    original_means={}
    for season in ("winter","summer"):
        group=original["season_groups"][season]
        original_means[season]=_finite(
            group["metrics"]["solar_over_clock"]["mean"],
            f"original.{season}.solar_over_clock"
        )
        planned=evidence[f"known_primary_{season}_solar_gain"]
        if abs(original_means[season]-planned)>1e-12:
            raise ValueError("original locked mean log gain differs from plan")
    rows=[]
    total_in_report=0
    total_problem_group=0
    provisional=[]
    eligibility_fail_counts=Counter()
    for name,raw in sorted(taxa.items()):
        if not isinstance(name,str) or not name.strip():
            raise ValueError("invalid taxon name in original first receipt")
        n=_nonnegative_int(raw["scored_images_after_dedup"],f"{name}.scored")
        total_in_report+=n
        winter=raw["winter"]; summer=raw["summer"]
        w_sites=_nonnegative_int(winter["unique_physical_site_count"],"winter site count")
        s_sites=_nonnegative_int(summer["unique_physical_site_count"],"summer site count")
        w=_finite(winter["metrics"]["solar_over_clock"]["mean"],f"{name}.winter")
        s=_finite(summer["metrics"]["solar_over_clock"]["mean"],f"{name}.summer")
        excluded_name=(
            name in disallowed or name.endswith(" sp.")
            or len(name.split())!=2
        )
        provisional_flag=(not excluded_name and n>=floor_events
                          and min(w_sites,s_sites)>=floor_sites)
        if excluded_name:eligibility_fail_counts["excluded_taxon_status"]+=1
        elif n<floor_events:eligibility_fail_counts["insufficient_total_events"]+=1
        elif min(w_sites,s_sites)<floor_sites:eligibility_fail_counts["insufficient_season_sites"]+=1
        if name in disallowed:total_problem_group+=n
        row={
            "taxon":name,
            "total_scored_events_both_future_years":n,
            "winter_distinct_site_count":w_sites,
            "summer_distinct_site_count":s_sites,
            "winter_solar_over_clock":w,
            "summer_solar_over_clock":s,
            "winter_minus_summer":w-s,
            "provisional_site_event_screen_pass":provisional_flag,
            "distinct_scored_future_year_count":None,
            "requires_two_scored_future_years_verified":False,
            "winter_summer_same_physical_site_pair_verified":False,
        }
        rows.append(row)
        if provisional_flag:provisional.append(row)
    scored_total=_nonnegative_int(data["scored_heldout_events"],"scored_heldout_events")
    if total_in_report>scored_total:
        raise ValueError("taxon descriptive subtotal exceeds first-run scored total")
    if not provisional:
        raise ValueError("no taxa pass even the incomplete prospective site/event screen")
    w_arr=np.asarray([r["winter_solar_over_clock"] for r in provisional])
    s_arr=np.asarray([r["summer_solar_over_clock"] for r in provisional])
    diff=w_arr-s_arr
    def mean(values):return float(np.mean(values))
    def q(values):
        return {label:float(np.quantile(values,p))
                for label,p in (("q25",.25),("median",.5),("q75",.75))}
    return {
        "schema_version":1,
        "method_version":METHOD_VERSION,
        "inference_category":"POST_OUTCOME_DESCRIPTION_ONLY",
        "original_receipt_sha256":digest,
        "original_first_workflow_run":37747931559,
        "original_status_unchanged":data["status"],
        "original_heldout_primary_site_count":data["heldout_site_count"],
        "original_all_site_weighted_gains":original_means,
        "original_both_season_solar_superiority_supported":False,
        "taxa_reported_in_original":len(rows),
        "taxa_total_events_in_original_taxon_summaries":total_in_report,
        "original_scored_events":scored_total,
        "events_not_in_species_descriptive_summaries":scored_total-total_in_report,
        "known_nonwild_or_unresolved_taxa_event_total":total_problem_group,
        "known_nonwild_or_unresolved_taxa_fraction_all_scored":total_problem_group/scored_total,
        "taxon_screen": {
            "min_sites_per_season":floor_sites,
            "min_events_across_future_years":floor_events,
            "require_2_future_years":True,
            "per_taxon_future_year_count_available":False,
            "site_year_taxon_roster_available":False,
            "fully_eligible_taxa_count":None,
            "provisional_site_event_pass_count":len(provisional),
            "provisional_total_events":sum(x["total_scored_events_both_future_years"] for x in provisional),
            "candidate_exclusions_by_reason":dict(eligibility_fail_counts),
            "status":"HOLD_CANNOT_VERIFY_PER_TAXON_TWO_FUTURE_YEAR_RULE",
        },
        "provisional_taxon_equal_weight": {
            "winter_mean":mean(w_arr),
            "summer_mean":mean(s_arr),
            "winter_minus_summer_mean":mean(diff),
            "winter_minus_summer_quartiles":q(diff),
            "winter_positive_summer_negative_count":sum(
                r["winter_solar_over_clock"]>0 and r["summer_solar_over_clock"]<0
                for r in provisional
            ),
            "winter_negative_summer_positive_count":sum(
                r["winter_solar_over_clock"]<0 and r["summer_solar_over_clock"]>0
                for r in provisional
            ),
            "both_negative_count":sum(
                r["winter_solar_over_clock"]<0 and r["summer_solar_over_clock"]<0
                for r in provisional
            ),
            "both_positive_count":sum(
                r["winter_solar_over_clock"]>0 and r["summer_solar_over_clock"]>0
                for r in provisional
            ),
            "species":provisional,
            "not_original_primary_estimand":True,
            "significance_or_coverage_certified":False,
            "composition_explains_sign_reversal_established":False,
        },
        "all_original_species_rows":rows,
        "site_taxon_season_year_joint_cells_available":False,
        "exact_matched_site_or_within_taxon_season_composition_decomposition_identified":False,
        "no_raw_zenodo_source_reopened":True,
        "no_new_heldout_model_scores_computed":True,
        "original_ecological_v0_v1_v2_inference_reclassified":False,
        "all_active_odsp_qualified_routes_unchanged":True,
    }


def run_from_files(
    original_json_path:Path,
    plan_path:Path,
    output_path:Path,
)->dict[str,Any]:
    """Audit immutable first-result bytes, write descriptive receipt."""
    frozen=plan_path.read_bytes()
    plan=json.loads(frozen)
    result=analyze_pinned_taxonomic_receipt(original_json_path.read_bytes(),plan)
    output={**result,"analysis_plan_sha256":hashlib.sha256(frozen).hexdigest()}
    output_path.write_text(
        json.dumps(output,sort_keys=True,ensure_ascii=False,indent=2,
                   allow_nan=False)+"\n",encoding="utf-8"
    )
    return output
