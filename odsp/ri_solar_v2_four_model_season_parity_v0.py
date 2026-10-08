"""Post-result FOUR-model season-parity identity from the first RI v2 receipt.

No ZIP download, camera data, model refitting, bootstrap, p-value or
post-hoc group/taxon filtering. We compare matched heldout event targets:
  S-C   = pooled-solar - pooled-clock
  SS-S  = season-solar - pooled-solar
  CS-C  = season-clock - pooled-clock
  SS-CS = (S-C)+(SS-S)-(CS-C)
All means are the ORIGINAL same-site-weighted per-season means,
so this contrast identity holds by linearity of the score aggregation.

Even a negative adjusted MEAN cannot be labelled significant merely by
subtracting three separately calculated confidence-bound endpoints:
their joint site-level covariance is absent from the first receipt.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

VERSION="ri_solar_v2_frozen_four_model_season_parity_v0"
RUN=37747931559
SHA="5d4bca0efc079ec3ae58d1062d4c1fb4c0b6476b64d56eead6d79e39ae83edab"
EXPECTED_STATUS="EXPLORATORY_NOT_SUPPORTED_OR_UNAVAILABLE"
METHOD="odsp-ri-solar-vs-clock-yearseason-v2-exploratory"


def _finite(value:object,name:str)->float:
    if isinstance(value,bool) or not isinstance(value,(int,float)):
        raise ValueError(f"{name} must be a real number")
    result=float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _check_plan(plan:Mapping[str,object])->None:
    if (not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("analysis_id")!=VERSION
        or plan.get("status")!="POST_OUTCOME_ALGEBRAIC_AUDIT_NO_NEW_ECOLOGICAL_DATA"):
        raise ValueError("unrecognized frozen four-model audit contract")
    ref=plan.get("source",{})
    if (not isinstance(ref,Mapping)
        or ref.get("first_original_run_id")!=RUN
        or ref.get("original_json_sha256")!=SHA
        or ref.get("original_scientific_status")!=EXPECTED_STATUS
        or ref.get("original_heldout_site_count")!=43
        or ref.get("original_scored_events")!=19916
        or ref.get("re_download_of_wildlife_source_allowed") is not False):
        raise ValueError("original first-result anchor changed")
    declared=plan.get("frozen_scoring_contrasts",{})
    if (
        not isinstance(declared,Mapping) or
        declared.get("SS_vs_CS")!="(S_vs_C)+(SS_vs_S)-(CS_vs_C)"
    ):
        raise ValueError("frozen four-model score algebra changed")


def audit_four_model_parity(
    original_first_result_json:bytes,
    frozen_plan:Mapping[str,object],
)->dict[str,Any]:
    """Reproduce a purely algebraic ecological diagnostic, no new model fit."""
    _check_plan(frozen_plan)
    if not isinstance(original_first_result_json,bytes):
        raise ValueError("original result must be original bytes")
    digest=hashlib.sha256(original_first_result_json).hexdigest()
    if digest!=SHA:
        raise ValueError("original first-run JSON SHA256 mismatch")
    try:
        original=json.loads(original_first_result_json)
    except (UnicodeDecodeError,json.JSONDecodeError) as exc:
        raise ValueError("invalid immutable original result") from exc
    if (
        original.get("method_version")!=METHOD
        or original.get("status")!=EXPECTED_STATUS
        or original.get("scored_heldout_events")!=19916
        or original.get("heldout_site_count")!=43
        or original.get("primary_heldout_solar_clock",{}).get("solar_transfer_both_seasons_positive") is not False
    ):
        raise ValueError("original v2 scientific method, result or site/sample status changed")
    first=original["primary_heldout_solar_clock"]
    groups=first["season_groups"]
    per_season={}
    for season in ("winter","summer"):
        if season not in groups:
            raise ValueError(f"original {season} outcome group missing")
        item=groups[season]
        if item.get("unique_physical_site_count")!=43:
            raise ValueError("season-specific physical heldout site count changed")
        metrics=item["metrics"]
        required=(
            "solar_over_clock",
            "solar_season_over_solar",
            "clock_season_over_clock",
            "true_solar_over_wrong_sun",
        )
        component={}
        for key in required:
            component[key]=_finite(
                metrics[key]["mean"],
                f"{season}.{key}.mean",
            )
        raw=component["solar_over_clock"]
        solar_increment=component["solar_season_over_solar"]
        clock_increment=component["clock_season_over_clock"]
        adjusted=raw+solar_increment-clock_increment
        clock_advantage=clock_increment-solar_increment
        per_season[season]={
            "original_same_site_weighted_pooled_solar_minus_clock":raw,
            "additional_gain_from_conditioning_solar_on_season":solar_increment,
            "additional_gain_from_conditioning_clock_on_season":clock_increment,
            "clock_season_information_gain_minus_solar_season_information_gain":clock_advantage,
            "season_conditional_solar_minus_clock":adjusted,
            "difference_between_conditional_and_unconditional_comparisons":solar_increment-clock_increment,
            "same_site_weighted_negative_control_true_solar_minus_wrong_sun":component["true_solar_over_wrong_sun"],
            "season_conditional_solar_preferred_by_point_mean":adjusted>0,
            "confidence_interval_for_season_conditional_difference_available":False,
            "inference_that_conditional_clock_advantage_is_statistically_significant":False,
            "components_are_from_same_original_clock_target":True,
        }
    winter=per_season["winter"]
    summer=per_season["summer"]
    if not (
        winter["original_same_site_weighted_pooled_solar_minus_clock"]>0
        and summer["original_same_site_weighted_pooled_solar_minus_clock"]<0
    ):
        raise ValueError("known first pooled season sign pattern changed")
    return {
        "schema_version":1,
        "method_version":VERSION,
        "status":"POST_OUTCOME_FOUR_MODEL_PARITY_ALGEBRA_ONLY",
        "source_first_workflow_run_id":RUN,
        "source_first_result_sha256":digest,
        "original_scientific_status":EXPECTED_STATUS,
        "original_both_seasons_solar_superiority_supported":False,
        "original_heldout_sites":43,
        "original_scored_detections":19916,
        "comparisons":per_season,
        "winter_pooled_solar_advantage_reverses_under_equal_season_information":(
            winter["season_conditional_solar_minus_clock"]<0
        ),
        "clock_season_model_higher_mean_than_solar_season_in_both_groups":(
            all(per_season[s]["season_conditional_solar_minus_clock"]<0
                for s in ("winter","summer"))
        ),
        "causal_photoperiod_mechanism_identified":False,
        "comparison_significance_or_coverage_qualified":False,
        "adjusted_difference_site_bootstrap_covariance_available":False,
        "separate_component_confidence_bounds_can_be_subtracted":False,
        "reopened_wildlife_source_zip_or_individual_detections":False,
        "refitted_models_or_recomputed_scores":False,
        "post_result_positive_group_selection_done":False,
        "original_source_ecological_endpoint_reclassified":False,
        "qualified_process_v5_or_source_v0_route_modified":False,
    }
