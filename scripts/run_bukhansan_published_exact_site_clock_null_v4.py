#!/usr/bin/env python3
"""Exact conditional *record-label* null for public Bukhansan 11-site clock bins.

SOURCE: Jeong et al. 2025, DOI 10.14397/jals.2025.59.5.111,
Tables 1-2, original 11 station codes x 24 hour rows; source-derived,
independently author-margin-checked v1 11x3 table. This program is
POST-PUBLICATION exploratory and does NOT use original Uljin 41 dates.

The null conditions on EACH camera's species totals and three combined
clock-period totals. It enumerates ALL possible within-camera 2x3 count
tables with multivariate hypergeometric COMBINATORIAL weights, and
convolves integer site score distributions EXACTLY, no RNG, no pseudocount.

The resulting 'probability' is a FORMAL conditional photographed-record
exchangeability diagnostic. Camera photos/animals are not proven independent
or exchangeable; this is NOT a valid wildlife population p-value, not a
test of direct competition, and not a station/animal clustered analysis.
"""
from __future__ import annotations

from collections import Counter
from itertools import product
import json
from math import comb, isclose, prod
from pathlib import Path

from run_bukhansan_author_published_same_camera_windows_v1 import (
    read_source_contract, SITES
)
from run_bukhansan_published_joint_space_clock_overlap_v3 import (
    compute as compute_original_distribution, PERIODS
)

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "BUKHANSAN_PUBLISHED_SITE_CONDITIONAL_CLOCK_NULL_V4_CONTRACT.json"
SOURCE = ROOT / "BUKHANSAN_PUBLISHED_SITE_HOUR_WINDOWS_V1_CONTRACT.json"
PREVIOUS = ROOT / "BUKHANSAN_PUBLIC_JOINT_SPACE_CLOCK_OVERLAP_V3_CONTRACT.json"
STATUS = "EXACT_CONDITIONAL_PUBLISHED_RECORD_CLOCK_NULL_NOT_ANIMAL_INFERENCE"


def validate(plan: dict) -> None:
    if (
        plan.get("schema_version") != 1
        or plan.get("contract_id") !=
            "bukhansan_published_11_camera_exact_conditional_record_clock_null_v4"
        or plan.get("stage") !=
            "FROZEN_AFTER_FULL_AUTHOR_TABLE_EXPOSURE_POSTPUBLICATION_EXPLORATORY"
        or plan.get("author_paper_doi") != "10.14397/jals.2025.59.5.111"
        or plan.get("public_author_derived_source") != SOURCE.name
        or plan.get("preceding_observed_route") != PREVIOUS.name
        or plan.get("fixed_clock_bins") != list(PERIODS)
        or plan.get("fixed_camera_roster") != list(SITES)
        or plan.get("fixed_species") != ["water_deer", "wild_boar"]
    ):
        raise ValueError("HOLD_POST_SOURCE_CONDITIONAL_NULL_CONTRACT_CHANGED")
    null = plan.get("null")
    if (
        not isinstance(null, dict)
        or null.get("max_supported_integer_states") != 50000
        or null.get("max_camera_cell_count") != 1000
        or null.get("global_score") !=
            "S=sum_camera,clock min(Nboar*w_camera_clock,Nwater*b_camera_clock)"
        or null.get("one_sided_direction") !=
            "Greater conditional detected-time dissimilarity D means S <= observed original table score"
    ):
        raise ValueError("HOLD_CONDITIONAL_NULL_REFERENCE_PROCESS_CHANGED")
    limits=plan.get("source_holds")
    if (not isinstance(limits,dict) or len(limits)!=11
        or any(v is not False for v in limits.values())):
        raise ValueError("HOLD_UNJUSTIFIED_WILDLIFE_SIGNIFICANCE_OR_ORIGINAL_SOURCE")


def score_integer(water: tuple[int, ...], combined: tuple[int, ...],
                  n_water: int, n_boar: int) -> int:
    if (len(water)!=3 or len(combined)!=3 or n_water<=0 or n_boar<=0
        or any(not isinstance(v,int) or v<0 for v in water+combined)
        or any(w>t for w,t in zip(water,combined))):
        raise ValueError("HOLD_INVALID_SITE_CLOCK_SOURCE_SCORE")
    return sum(min(n_boar*w,n_water*(t-w))
               for w,t in zip(water,combined))


def enumerate_camera_null(three_combined: tuple[int,int,int], water_total: int,
                          n_water:int, n_boar:int
                          ) -> tuple[int,dict[int,int]]:
    """Return EXACT combinatorial denominator and integer score-weight PMF.

    For any allocation x=(x1,x2,x3), weight is
       product binomial(combined_bin, water_bin)
    divided by binomial(total, fixed site Water count).
    This is NOT uniform weighting over feasible contingency tables.
    """
    if (len(three_combined)!=3 or
        any(not isinstance(x,int) or x<0 for x in three_combined) or
        any(x>1000 for x in three_combined) or
        not isinstance(water_total,int) or
        water_total<0 or water_total>sum(three_combined)):
        raise ValueError("HOLD_INVALID_PUBLISHED_SITE_CONDITIONING")
    t0,t1,t2=three_combined
    denominator=comb(sum(three_combined),water_total)
    probs:dict[int,int]={}
    for w0 in range(max(0,water_total-t1-t2),min(t0,water_total)+1):
        for w1 in range(max(0,water_total-w0-t2),min(t1,water_total-w0)+1):
            w2=water_total-w0-w1
            if not (0<=w2<=t2):
                continue
            waters=(w0,w1,w2)
            weight=prod(comb(t,w) for t,w in zip(three_combined,waters))
            score=score_integer(waters,three_combined,n_water,n_boar)
            probs[score]=probs.get(score,0)+weight
    if (not probs or any(v<=0 for v in probs.values())
        or sum(probs.values())!=denominator):
        raise ValueError("HOLD_SITE_MULTIVARIATE_HYPERGEOMETRIC_MASS_ERROR")
    return denominator,probs


def convolve_exact(site_distributions: list[tuple[str,int,dict[int,int]]],
                   state_cap:int) -> tuple[int,dict[int,int]]:
    pmf:dict[int,int]={0:1}
    denominator=1
    for name,site_den,site_pdf in sorted(site_distributions,key=lambda t:len(t[2])):
        if sum(site_pdf.values())!=site_den:
            raise ValueError("HOLD_CORRUPTED_LOCAL_NULL_WEIGHTS_"+name)
        next_pmf:dict[int,int]={}
        for old_score,old_weight in pmf.items():
            for site_score,site_weight in site_pdf.items():
                key=old_score+site_score
                next_pmf[key]=next_pmf.get(key,0)+old_weight*site_weight
        denominator*=site_den
        if len(next_pmf)>state_cap:
            raise ValueError("HOLD_EXACT_NULL_SUPPORT_EXCEEDS_PREDECLARED_CAP")
        if sum(next_pmf.values())!=denominator:
            raise ValueError("HOLD_EXACT_INTEGER_CONVOLUTION_MASS_ERROR")
        pmf=next_pmf
    return denominator,pmf


def quantile_gap(pmf:dict[int,int],denominator:int,spatial_score:int,
                 product_species_totals:int,q:float)->float:
    """Invert discrete CDF for EXTRA GAP, ascending gap/descending score."""
    if not 0<q<1:
        raise ValueError("HOLD_INVALID_EXACT_CONDITIONAL_QUANTILE")
    running=0
    for score,weight in sorted(pmf.items(),reverse=True):
        running+=weight
        if running/denominator>=q:
            return (spatial_score-score)/product_species_totals
    raise ValueError("HOLD_CONDITIONAL_QUANTILE_OUTSIDE_SUPPORT")


def analyze(plan:dict,source:dict,v3_plan:dict) -> dict:
    validate(plan)
    rows=read_source_contract(source)
    original=compute_original_distribution(v3_plan,source)
    if original["status"]!="PUBLISHED_JOINT_SITE_CLOCK_RECORDED_OVERLAP_REFINEMENT_ONLY":
        raise ValueError("HOLD_PRECEDING_OBSERVED_SOURCE_NOT_REPRODUCIBLE")
    n_water=184
    n_boar=273
    scale=n_water*n_boar
    spatial_score=0
    observed_score=0
    local_out=[]
    null_distributions=[]
    for r in rows:
        w=tuple(r["water_deer"][z] for z in PERIODS)
        b=tuple(r["wild_boar"][z] for z in PERIODS)
        t=tuple(wi+bi for wi,bi in zip(w,b))
        wtotal=sum(w)
        btotal=sum(b)
        if wtotal+btotal!=sum(t):
            raise ValueError("HOLD_SOURCE_STATION_PHOTO_TOTAL")
        spatial_score+=min(n_boar*wtotal,n_water*btotal)
        site_observed_score=score_integer(w,t,n_water,n_boar)
        observed_score+=site_observed_score
        local_spatial=min(n_boar*wtotal,n_water*btotal)
        denominator,weights=enumerate_camera_null(t,wtotal,n_water,n_boar)
        if site_observed_score not in weights:
            raise ValueError("HOLD_OBSERVED_CAMERA_ALLOCATION_NOT_IN_EXACT_SUPPORT")
        exact_site_score_mean=sum(s*wght for s,wght in weights.items())/denominator
        observed_local_gap=(local_spatial-site_observed_score)/scale
        expected_local_gap=(local_spatial-exact_site_score_mean)/scale
        local_out.append({
            "public_camera_code":r["site"],
            "source_water_records":wtotal,
            "source_boar_records":btotal,
            "source_fixed_three_clock_bin_total":list(t),
            "number_of_exact_local_integer_score_states":len(weights),
            "observed_additional_clock_discrepancy":round(observed_local_gap,9),
            "exact_conditional_null_expected_additional_discrepancy":round(expected_local_gap,9),
            "POSTHOC_exact_one_sided_tail_of_local_null_not_site_biological_p":
                round(sum(weight for score,weight in weights.items()
                          if score<=site_observed_score)/denominator,9),
            "individual_photograph_independence_assumed_only_for_formal_null":True,
            "population_site_hypothesis_confirmed":False,
        })
        null_distributions.append((r["site"],denominator,weights))

    reported=original["pooled_recorded_overlap"]
    observed_gap=(spatial_score-observed_score)/scale
    if not (isclose(spatial_score/scale,reported["camera_space_only"],abs_tol=3e-9)
        and isclose(observed_score/scale,reported["joint_camera_x_clock_window"],abs_tol=3e-9)
        and isclose(observed_gap,reported["spatial_first_decomposition"]
                    ["ADDITIONAL_clock_given_spatial_refinement_TV"],abs_tol=3e-9)):
        raise ValueError("HOLD_OBSERVED_V3_OVERLAP_AND_V4_EXACT_SCORE_DIFFER")

    denominator,pmf=convolve_exact(null_distributions,
                                  plan["null"]["max_supported_integer_states"])
    exact_tail_numerator=sum(wght for score,wght in pmf.items()
                             if score<=observed_score)
    if not (0<exact_tail_numerator<=denominator):
        raise ValueError("HOLD_CONDITIONAL_TAIL_UNDEFINED")
    null_expected_score=sum(
        sum(s*wght for s,wght in weights.items())/d
        for _,d,weights in null_distributions
    )
    expected_extra_gap=(spatial_score-null_expected_score)/scale
    qlo=quantile_gap(pmf,denominator,spatial_score,scale,.025)
    qmed=quantile_gap(pmf,denominator,spatial_score,scale,.5)
    qhi=quantile_gap(pmf,denominator,spatial_score,scale,.975)
    if not qlo<=qmed<=qhi:
        raise ValueError("HOLD_EXACT_NULL_QUANTILES_NOT_ORDERED")
    g19=next(item for item in local_out if item["public_camera_code"]=="G19")
    return {
        "status":STATUS,
        "primary_source_doi":plan["author_paper_doi"],
        "scope":plan["stage"],
        "source_record_totals":{"water_deer":n_water,"wild_boar":n_boar},
        "all_11_source_camera_station_roster_retained":list(SITES),
        "source_fixed_site_and_clock_margins_preserved":True,
        "exact_integer_conditional_null":{
            "mechanism":"WITHIN each site species labels randomly allocated among fixed clock bins, weighted by multivariate hypergeometric combinatorial counts",
            "total_variation_statistic":"observed O_site−O_joint",
            "observed_site_only_overlap":round(spatial_score/scale,9),
            "observed_joint_site_clock_overlap":round(observed_score/scale,9),
            "observed_additional_clock_discrepancy":round(observed_gap,9),
            "EXACT_null_expected_additional_clock_discrepancy":round(expected_extra_gap,9),
            "observed_minus_null_mean_additional_discrepancy":round(
                observed_gap-expected_extra_gap,9),
            "EXACT_null_conditional_gap_quantiles_2p5_50_97p5":[
                round(qlo,9),round(qmed,9),round(qhi,9)],
            "EXACT_one_sided_P_null_gap_at_least_observed_NOT_BIOLOGICAL_P":
                round(exact_tail_numerator/denominator,12),
            "exact_integer_conditional_tail_numerator":str(exact_tail_numerator),
            "exact_integer_conditional_probability_denominator":str(denominator),
            "total_integer_supported_global_scores":len(pmf),
            "original_observed_integer_overlap_score":observed_score,
            "finite_photo_label_exchangeability_required_but_NOT_independently_validated":True,
            "independently_replicated_biological_effect_significance_established":False,
        },
        "original_11_published_camera_local_conditional_nulls":local_out,
        "source_selected_G19_exploratory_local_null":{
            "observed_additional_gap":g19["observed_additional_clock_discrepancy"],
            "exact_expected_gap":g19["exact_conditional_null_expected_additional_discrepancy"],
            "POSTHOC_local_one_sided_tail_NOT_MULTIPLICITY_ADJUSTED":
                g19["POSTHOC_exact_one_sided_tail_of_local_null_not_site_biological_p"],
            "source_site_selected_after_outcomes":True,
            "population_avoidance_effect_identified":False,
        },
        "source_photo_record_independence_verified":False,
        "source_physical_camera_operation_hours_verified":False,
        "real_2022_Uljin_fixed_41_date_pairs_tested":False,
        "ecological_temporal_partition_confirmed":False,
    }


if __name__=="__main__":
    output=analyze(json.loads(PLAN.read_text()),json.loads(SOURCE.read_text()),
                   json.loads(PREVIOUS.read_text()))
    print(json.dumps(output,ensure_ascii=False,indent=2,sort_keys=True))
