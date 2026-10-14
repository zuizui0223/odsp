#!/usr/bin/env python3
"""Unique integers? 2025 Bukhansan publicly reported 457 photo marginals.

IMPORTANT: This is conditional INVERSE AGGREGATION, not an original dataset.
Only if all 457 images partition into exactly 4 species×habitat groups and
published fractions were formed from UNWEIGHTED integer photo counts, rounded
to 0.01 percentage point, is this reconstruction applicable. No camera
identity, photo independence, physical station-hours or causal habitat
partition is asserted. Any image-level Wald p is diagnostic ONLY, and must
not be cited as biological species×habitat inference.
"""
from __future__ import annotations

import argparse
from itertools import product
import json
from math import exp, log, sqrt, isclose
from pathlib import Path
import re
from statistics import NormalDist

from run_uljin_independent_korean_context_v0 import (
    official_kci_get, html_plain, verify_abstract
)

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "BUKHANSAN_PUBLISHED_INTEGER_RECONSTRUCTION_V0_CONTRACT.json"
NORM = NormalDist()
STATUS = "ONE_CONDITIONAL_INTEGER_TABLE_COMPATIBLE_WITH_PUBLISHED_ABSTRACT"


def parse_percent_basis_points(v: str) -> int:
    if not isinstance(v, str) or not re.fullmatch(r"\d{1,3}\.\d{2}", v):
        raise ValueError("HOLD_EXACT_TWO_DECIMAL_PERCENTAGE_REQUIRED")
    bp = int(v.split(".")[0])*100+int(v.split(".")[1])
    if not (0 < bp < 10000):
        raise ValueError("HOLD_INVALID_PUBLISHED_PERCENTAGE")
    return bp


def candidate_photo_counts(bp: int, max_total: int) -> list[tuple[int,int]]:
    """Positive (total, night) with round(100*night/total,2)==bp/100.

    Strict midpoint exclusion is explicit to avoid silently choosing
    round-half-up versus round-to-even, when not documented by authors.
    Here the candidate set has no relevant midpoint ties.
    """
    out=[]
    for n in range(2,max_total+1):
        around=(bp*n)//10000
        for k in range(max(1,around-1),min(n-1,around+2)+1):
            residual=abs(20000*k-2*bp*n)
            if residual==n:
                raise ValueError("HOLD_UNDISCLOSED_PERCENT_ROUNDING_TIE")
            if residual<n:
                out.append((n,k))
    return sorted(set(out))


def _check_contract(plan: dict) -> None:
    if (plan.get("schema_version")!=1
        or plan.get("contract_id")!="bukhansan_2025_public_457_images_integer_partition_v0"
        or plan.get("stage")!="POST_PUBLICATION_EXPLORATORY_CONDITIONAL_INVERSE_AGGREGATION"):
        raise ValueError("HOLD_INVALID_POST_PUBLICATION_SOURCE_CONTRACT")
    src=plan.get("source",{})
    if (src.get("doi")!="10.14397/jals.2025.59.5.111"
        or src.get("focal_analyzed_images_reported")!=457
        or src.get("all_camera_photos_reported")!=2529):
        raise ValueError("HOLD_PUBLIC_SOURCE_ID_AND_SAMPLE_N_CHANGED")
    declared=[
        ("Water deer","forest","70.27","29.73"),
        ("Wild boar","forest","70.85","29.15"),
        ("Water deer","wetland","83.64","16.36"),
        ("Wild boar","wetland","77.03","22.97")
    ]
    if not isinstance(plan.get("groups"),list) or [
        (g.get("taxon"),g.get("habitat"),g.get("rounded_night_percent"),g.get("rounded_day_percent"))
        for g in plan["groups"]] !=declared:
        raise ValueError("HOLD_FOUR_ORIGINAL_PUBLISHED_STRATA_CHANGED")
    if (not isinstance(plan.get("design_guards"),dict)
        or len(plan["design_guards"])!=10
        or any(x is not False for x in plan["design_guards"].values())):
        raise ValueError("HOLD_ECOLOGICAL_SCOPE_PROMOTION")
    if (src.get("night_and_day_exhaustive_categories_ASSUMPTION_NOT_INDEPENDENTLY_CONFIRMED") is not True
        or src.get("group_rows_all_part_of_457_ASSUMPTION_NOT_INDEPENDENTLY_CONFIRMED") is not True
        or src.get("percent_rounding_nearest_0p01_ASSUMPTION_NOT_INDEPENDENTLY_CONFIRMED") is not True
        or src.get("photo_independence_NOT_established") is not True
        or src.get("camera_effort_by_habitat_NOT_available") is not True):
        raise ValueError("HOLD_CRITICAL_INVERSE_ASSUMPTIONS")
    if "sum of four group photo counts EXACTLY 457" not in plan.get("partition_rule",""):
        raise ValueError("HOLD_AGGREGATE_PARTITION_RULE_UNDOCUMENTED")


def verify_public_kci_text(plan:dict, public_html:str)->dict:
    """Public KCI abstract, no source-bypassing or raw GPS."""
    ref={
        "doi":plan["source"]["doi"],
        "night_fraction_pct":{
            "water_deer_forest":70.27,
            "wild_boar_forest":70.85,
            "water_deer_wetland":83.64,
            "wild_boar_wetland":77.03
        }
    }
    verified=verify_abstract(public_html,ref,"bukhansan_2025")
    text=html_plain(public_html).lower()
    start=text.find(plan["source"]["source_anchor"])
    if start<0:
        raise ValueError("HOLD_KCI_EXACT_ENGLISH_ABSTRACT_NOT_FOUND")
    extract=text[start:start+5000]
    if "2,529" not in extract or "457 images" not in extract:
        raise ValueError("HOLD_ORIGINAL_PUBLIC_ABSTRACT_IMAGE_COUNTS_MISSING")
    actual_percentages=[
        float(x) for x in re.findall(r"(?<!\d)(\d{1,3}\.\d{2})\s*%",extract)
    ]
    for group in plan["groups"]:
        for field in ("rounded_night_percent","rounded_day_percent"):
            value=float(group[field])
            if not any(isclose(x,value,abs_tol=1e-10,rel_tol=0) for x in actual_percentages):
                raise ValueError("HOLD_KCI_REPORTED_PERCENT_NOT_RECORDED_"+field)
    return {
        "official_publisher_abstract_rechecked":verified["public_source_verified"],
        "all_8_day_night_published_percentages_found":True,
        "all_457_of_2529_sample_context_verified":True,
        "KCI_original_event_table_read":False
    }


def reconstruct(plan:dict, authenticated_html:str|None)->dict:
    _check_contract(plan)
    if authenticated_html is None:
        return {"status":"HOLD_ORIGINAL_KCI_ABSTRACT_NOT_ATTESTED",
                "reconstructed_photo_table_as_empirical_source":False}
    source=verify_public_kci_text(plan,authenticated_html)
    total=plan["source"]["focal_analyzed_images_reported"]
    slots=plan["groups"]
    bp=[]
    options=[]
    for g in slots:
        nbp=parse_percent_basis_points(g["rounded_night_percent"])
        dbp=parse_percent_basis_points(g["rounded_day_percent"])
        if nbp+dbp!=10000:
            raise ValueError("HOLD_DAY_NIGHT_PUBLISHED_PERCENTS_NOT_COMPLEMENTARY")
        bp.append(nbp)
        options.append(candidate_photo_counts(nbp,total))
    n_solutions=0
    chosen=None
    for candidate in product(*options):
        if sum(x[0] for x in candidate)!=total:
            continue
        n_solutions+=1
        if n_solutions==1:
            chosen=candidate
    if n_solutions!=1 or chosen is None:
        return {"status":"HOLD_NOT_UNIQUELY_RECONSTRUCTIBLE_UNDER_ASSUMPTIONS",
                "candidate_group_option_counts":[len(o) for o in options],
                "number_of_exhaustive_integer_tables":n_solutions,
                "genuine_raw_photo_records_loaded":False}
    cells={}
    displayed=[]
    for g,(n,k) in zip(slots,chosen):
        key=(g["taxon"],g["habitat"])
        if key in cells or not 0<k<n:
            raise ValueError("HOLD_DUPLICATE_OR_ZERO_PHOTO_CELL")
        cells[key]={"night":k,"day":n-k,"total":n}
        displayed.append({
            "taxon":key[0],"habitat":key[1],
            "CONDITIONAL_number_of_photos":n,
            "CONDITIONAL_night_photos":k,
            "CONDITIONAL_day_photos":n-k,
            "reconstructed_night_percent":round(100*k/n,8),
            "source_published_rounded_percent":g["rounded_night_percent"]
        })
    if sum(c["total"] for c in cells.values())!=457:
        raise ValueError("HOLD_RECONSTRUCTION_TOTAL_MISMATCH")

    # Conditional PHOTO distributions, not abundance, actual movement,
    # or independent camera/source event data. Split data by species/habitat.
    wt={s:sum(cells[(s,h)]["total"] for h in ("forest","wetland"))
        for s in ("Water deer","Wild boar")}
    pw={(s,h):cells[(s,h)]["night"]/cells[(s,h)]["total"]
        for s in wt for h in ("forest","wetland")}
    ww={(s,h):cells[(s,h)]["total"]/wt[s]
        for s in wt for h in ("forest","wetland")}
    pooled={s:sum(cells[(s,h)]["night"] for h in ("forest","wetland"))/wt[s]
            for s in wt}
    diff=pooled["Water deer"]-pooled["Wild boar"]
    within=sum(.5*(ww["Water deer",h]+ww["Wild boar",h])*
               (pw["Water deer",h]-pw["Wild boar",h])
               for h in ("forest","wetland"))
    composition=sum(.5*(pw["Water deer",h]+pw["Wild boar",h])*
                    (ww["Water deer",h]-ww["Wild boar",h])
                    for h in ("forest","wetland"))
    if not isclose(within+composition,diff,rel_tol=0,abs_tol=1e-13):
        raise ValueError("HOLD_SYMMETRIC_KITAGAWA_IDENTITY")

    # Diagnostic ONLY. Incorrect as biological population uncertainty if
    # photos repeat the same animals/cameras. Valid as a simple conditional
    # independent-BERNOULLI PHOTO idealization, not station-clustered.
    wF,bF,wM,bM=(cells[("Water deer","forest")],
                 cells[("Wild boar","forest")],
                 cells[("Water deer","wetland")],
                 cells[("Wild boar","wetland")])
    ORW=(wM["night"]/wM["day"])/(wF["night"]/wF["day"])
    ORB=(bM["night"]/bM["day"])/(bF["night"]/bF["day"])
    interaction=ORW/ORB
    se=sqrt(sum(1/c[z] for c in (wF,bF,wM,bM) for z in ("night","day")))
    z=log(interaction)/se
    p=2*NORM.cdf(-abs(z))
    critical=NORM.inv_cdf(.975)
    naive_ci=[exp(log(interaction)-critical*se),
              exp(log(interaction)+critical*se)]
    equal_weights=(pw["Water deer","forest"]+pw["Water deer","wetland"]
                   -pw["Wild boar","forest"]-pw["Wild boar","wetland"])/2
    return {
        "status":STATUS,
        "source_validation":source,
        "source_doi":plan["source"]["doi"],
        "all_image_count":plan["source"]["all_camera_photos_reported"],
        "focal_image_count":total,
        "group_candidate_count_if_independently_considered":[len(o) for o in options],
        "number_of_all_integer_solutions_after_total_constraint":n_solutions,
        "only_integer_solution_under_EXPLICIT_UNVERIFIED_assumptions":displayed,
        "taxon_photo_marginal_total":wt,
        "taxon_photo_wetland_representation": {
            s:round(ww[s,"wetland"],9) for s in wt
        },
        "published_conditional_night_fraction_by_group": {
            s+"_"+h:round(pw[s,h],9)
            for s in wt for h in ("forest","wetland")
        },
        "photo_pooled_night_fractions_if_partition_is_complete":{
            s:round(pooled[s],9) for s in wt
        },
        "symmetric_kitagawa_DECOMPOSITION_OF_PHOTO_MARGINS_ONLY":{
            "observed_pooled_species_difference_percentage_points":round(100*diff,9),
            "within_habitat_distribution_component_pp":round(100*within,9),
            "photo_habitat_mix_component_pp":round(100*composition,9),
            "photo_habitat_mix_share_of_pooled_difference":round(composition/diff,9),
            "same_50_50_habitat_standardized_difference_pp":round(100*equal_weights,9),
            "proof_components_sum_to_pooled_difference":True,
            "biological_causal_partition_identified":False
        },
        "purely_naive_photo_independence_DIAGNOSTIC_NOT_ECOLOGICAL_INFERENCE":{
            "water_deer_wet_vs_forest_night_odds_ratio":round(ORW,9),
            "wild_boar_wet_vs_forest_night_odds_ratio":round(ORB,9),
            "ratio_of_species_habitat_odds_ratios":round(interaction,9),
            "independent_photo_WALD_log_OR_standard_error":round(se,9),
            "independent_photo_WALD_two_sided_p":round(p,9),
            "independent_photo_WALD_95_percent_CI":[round(x,9) for x in naive_ci],
            "this_is_NOT_a_valid_cluster_adjusted_biological_p_value":True,
            "unknown_camera_identity_and_repeated_animal_exposure":True
        },
        "original_real_event_records_obtained":False,
        "original_uljin_41_day_pairs_tested":False,
        "causal_species_habitat_temporal_effect_claimed":False
    }


STATUS="CONDITIONAL_UNIQUE_IMAGE_TABLE_AND_PHOTO_MIX_DECOMPOSITION_ONLY"

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--offline-KCI-html",type=Path)
    args=p.parse_args()
    try:
        plan=json.loads(PLAN.read_text())
        html=(args.offline_KCI_html.read_text() if args.offline_KCI_html
              else official_kci_get(plan["source"]["official_kci_url"]))
        result=reconstruct(plan,html)
    except (ValueError,KeyError,TypeError,OSError,TimeoutError) as exc:
        result={"status":"HOLD_KCI_INTEGER_INVERSION_NOT_VERIFIED",
                "error_class":type(exc).__name__,
                "original_raw_photo_records_accessed":False,
                "biological_p_value_established":False}
    print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))


if __name__=="__main__":
    main()
