#!/usr/bin/env python3
"""Empirical published 3-part diel pattern + conditional identifiability audit.

The 12 authentic aggregated Supplement 3 rows are verified by the existing
read-only MD5 provenance and table-consistency checker. We do NOT treat
different period-hours as observed camera on-time, and we do NOT infer
physical-station strata, optical camera-q, causal mechanisms or season effects.
All phase splits and sensitivity calculations are exploratory, after outcomes.
"""
from __future__ import annotations

import argparse
from itertools import combinations
import json
from math import isclose, log, sqrt
from pathlib import Path

from inspect_uljin_published_supp3_aggregate_v0 import download
from run_uljin_published_supp3_daypart_signatures_v0 import evaluate as evaluate_published

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CONTRACT = ROOT / "ULJIN_PUBLISHED_SUPPL3_DAYPART_SIGNATURE_V0_CONTRACT.json"
CONTRACT = ROOT / "ULJIN_PUBLISHED_SUPPL3_PHASE_IDENTIFIABILITY_V0_CONTRACT.json"
CATEGORIES = ("daytime", "crepuscular", "nighttime")
SPECIES = ("Long-tailed goral", "Siberian roe deer", "Water deer", "Wild boar")
STATUS = "PUBLISHED_THREE_PHASE_AND_CONDITIONAL_IDENTIFIABILITY_AUDITED"


def _safe_plan(plan: dict) -> None:
    if not isinstance(plan, dict) or plan.get("schema_version") != 1:
        raise ValueError("HOLD_INVALID_POST_PUBLICATION_PHASE_CONTRACT")
    if (
        plan.get("contract_id") != "uljin_published_supp3_three_part_phase_vs_camera_bias_v0"
        or plan.get("stage") != "POST_PUBLICATION_EXPLORATORY_NOT_FROZEN_BEFORE_SOURCES"
        or plan.get("parent_pr") != 264
        or plan.get("upstream_source_contract") !=
            "uljin_published_supp3_whole_period_rate_signature_v0"
        or plan.get("source_doi") != "10.3897/BDJ.14.e191556.suppl3"
        or plan.get("comparison_scope") != "FOUR_SPECIES_ALL_SIX_PAIRS_THREE_PERIODS"
        or plan.get("anchor_species") != ["Water deer", "Wild boar"]
        or plan.get("phase_categories") != list(CATEGORIES)
    ):
        raise ValueError("HOLD_PHASE_PLAN_MISMATCH")
    guards = plan.get("source_guards")
    if not isinstance(guards, dict) or len(guards) != 11 or any(x is not False for x in guards.values()):
        raise ValueError("HOLD_SOURCE_LIMITATIONS_MODIFIED")
    m = plan.get("models", {})
    if m.get("q_minmax_ratio_scenarios") != [1.0, 1.2, 1.5, 2.0, 2.25, 2.3, 2.5]:
        raise ValueError("HOLD_Q_SCENARIO_GRID_CHANGED_POST_OUTCOME")
    groups = m.get("site_mixture_counterexample", {})
    if (groups.get("group_A_common_night_probability") != 0.75
        or groups.get("group_B_common_night_probability") != 0.15):
        raise ValueError("HOLD_ABSTRACT_SITE_MIX_COUNTEREXAMPLE_CHANGED")


def _contrast(count_a: dict, count_b: dict, left: str, right: str) -> float:
    # Same calendar-length period denominators CANCEL in this species
    # ratio-of-ratios. No claim of camera on-time calibration follows.
    return ((count_a[left] / count_a[right]) /
            (count_b[left] / count_b[right]))


def inspect(plan: dict, source_plan: dict, authentic_supp3_zip: bytes) -> dict:
    _safe_plan(plan)
    if source_plan.get("contract_id") != plan["upstream_source_contract"]:
        raise ValueError("HOLD_PUBLIC_SOURCE_CONTRACT_UNEXPECTED")
    published = evaluate_published(source_plan, authentic_supp3_zip)
    if (published["status"] !=
            "REPRODUCED_PUBLISHED_DAYPART_POOLED_DESCRIPTIVE_SIGNATURE_ONLY"
        or not published["independently_verified_published_zip_md5"]
        or published["published_aggregate_rows"] != 12
        or published["reproduced_total_events"] != 4623
        or published["original_hourly_camera_operation_verified"]
        or published["frozen_original_41_day_pairs_tested"]):
        raise ValueError("HOLD_PUBLISHED_AGGREGATE_INCONSISTENT")

    profiles = published["species_profiles"]
    if [p["species"] for p in profiles] != list(SPECIES):
        raise ValueError("HOLD_ALL_FOUR_TAXA_REQUIRED")

    counts: dict[str, dict[str, int]] = {}
    all_species: list[dict] = []
    for p in profiles:
        taxon = p["species"]
        c = p["period_counts"]
        if (set(c) != set(CATEGORIES)
            or any(not isinstance(c[z], int) or c[z] <= 0 for z in CATEGORIES)):
            raise ValueError("HOLD_NONPOSITIVE_PUBLISHED_CELLS")
        rates = p["detections_per_100_published_calendar_period_hours"]
        highest = max(CATEGORIES, key=lambda z: rates[z])
        sorted_rates = sorted(rates.values(), reverse=True)
        counts[taxon] = c
        all_species.append({
            "species": taxon,
            "n_day": c["daytime"],
            "n_civil_twilight": c["crepuscular"],
            "n_night": c["nighttime"],
            "highest_detected_rate_per_published_period_hour": highest,
            "relative_difference_of_top_to_second_rate": round(
                sorted_rates[0]/sorted_rates[1] - 1, 9
            ),
            "civil_twilight_to_day_rate_ratio": round(
                rates["crepuscular"]/rates["daytime"], 9
            ),
            "night_to_civil_twilight_rate_ratio": round(
                rates["nighttime"]/rates["crepuscular"], 9
            ),
            "night_to_day_rate_ratio": round(
                rates["nighttime"]/rates["daytime"], 9
            ),
            "civil_twilight_equals_frozen_daylight_edge": False,
            "population_behavior_or_species_preference_inferred": False,
        })

    six = []
    for a, b in combinations(SPECIES, 2):
        day_twilight = _contrast(counts[a], counts[b],
                                 "crepuscular", "daytime")
        twilight_night = _contrast(counts[a], counts[b],
                                   "nighttime", "crepuscular")
        night_day = _contrast(counts[a], counts[b],
                              "nighttime", "daytime")
        if not isclose(day_twilight * twilight_night, night_day,
                       rel_tol=2e-13, abs_tol=2e-13):
            raise ValueError("HOLD_THREE_PART_DECOMPOSITION")
        six.append({
            "species_a": a,
            "species_b": b,
            "ratio_of_species_civil_twilight_day_odds": round(day_twilight, 9),
            "ratio_of_species_night_civil_twilight_odds": round(twilight_night, 9),
            "ratio_of_species_night_day_odds": round(night_day, 9),
            "three_part_identity_holds": True,
            "statistical_significance_estimated": False
        })

    water = counts["Water deer"]
    boar = counts["Wild boar"]
    R = _contrast(water, boar, "nighttime", "daytime")
    pair = next(x for x in six if x["species_a"] == "Water deer"
                and x["species_b"] == "Wild boar")
    max_pair = max(six, key=lambda item: abs(log(item["ratio_of_species_night_day_odds"])))
    if (max_pair is not pair or R <= 1):
        raise ValueError("HOLD_POSTHOC_REFERENCE_PAIR_CHANGED")

    # STRICT CONDITIONAL counterfactual: a common site and exposure
    # population and four positive effective q multipliers. If each q is
    # in [qmin,qmax], B=(q_WN/q_WD)/(q_BN/q_BD) is in [1/r^2,r^2],
    # where r=qmax/qmin. Actual site mixing, camera-on time and q are
    # unknown, so these are NOT empirical adjusted animal rates.
    scenarios = []
    for r in plan["models"]["q_minmax_ratio_scenarios"]:
        if r < 1:
            raise ValueError("HOLD_INVALID_Q_BOUNDS")
        scenarios.append({
            "hypothetical_qmax_over_qmin": r,
            "hypothetical_max_cross_species_night_day_q_factor": round(r*r, 9),
            "minimum_latent_ratio_IF_common_exposure_and_q_only": round(R/(r*r), 9),
            "maximum_latent_ratio_IF_common_exposure_and_q_only": round(R*r*r, 9),
            "observed_q_or_exposure_claimed": False,
        })

    # Construct one mathematical site-mixture witness for the exact
    # source day/night fractions. For every species, identical p(night)
    # in both abstract strata A and B, but DIFFERENT species mixture
    # fractions. Expected counts (fractional allowed) recreate all
    # source night/day marginal proportions exactly. These strata are
    # NOT identified with UJ1/UJ2 or any real physical camera.
    A = plan["models"]["site_mixture_counterexample"]["group_A_common_night_probability"]
    B = plan["models"]["site_mixture_counterexample"]["group_B_common_night_probability"]
    if not (0 < B < A < 1):
        raise ValueError("HOLD_COUNTEREXAMPLE_INVALID")
    witness = []
    for taxon in SPECIES:
        c = counts[taxon]
        expected_p = c["nighttime"]/(c["nighttime"]+c["daytime"])
        weight = (expected_p-B)/(A-B)
        reconstructed = weight*A+(1-weight)*B
        if not (0 < weight < 1 and isclose(expected_p,reconstructed,
                                            rel_tol=0,abs_tol=1e-14)):
            raise ValueError("HOLD_COUNTEREXAMPLE_DOES_NOT_MATCH_MARGINS")
        witness.append({
            "species":taxon,
            "published_detected_night_fraction_excluding_twilight":round(expected_p,9),
            "HYPOTHETICAL_fraction_of_detected_events_from_A":round(weight,9),
            "reconstructed_marginal_fraction":round(reconstructed,9),
        })

    return {
        "status": STATUS,
        "source": "PUBLISHED_ZENODO_SUPPLEMENT3_MD5_ATTESTED_AGGREGATE",
        "analysis_stage": plan["stage"],
        "source_supplement_doi": plan["source_doi"],
        "four_species_all_three_parts":all_species,
        "all_six_unordered_species_pairs":six,
        "all_four_source_profiles_peak_in_civil_twilight_per_published_period_hour":
            all(p["highest_detected_rate_per_published_period_hour"]=="crepuscular"
                for p in all_species),
        "water_deer_to_boar_three_part_ratio":{
            "twilight_to_day_between_species": pair["ratio_of_species_civil_twilight_day_odds"],
            "night_to_twilight_between_species": pair["ratio_of_species_night_civil_twilight_odds"],
            "night_to_day_between_species":round(R,9),
            "identity_verified":True,
            "posthoc_selected":True,
        },
        "conditional_effective_detector_q_sensitivity":{
            "equal_latent_ratio_tipping_qmax_over_qmin_IF_common_site_exposure":round(sqrt(R),9),
            "q_scenarios":scenarios,
            "q_is_observed_in_real_data":False,
            "site_mix_assumed_equal_in_conditional_formula":True,
        },
        "no_species_specific_within_stratum_phase_difference_counterexample":{
            "status":"EXACT_EXPECTED_TWO_ABSTRACT_GROUPS_DAY_NIGHT_ONLY",
            "group_A_identical_night_probability_for_all_species":A,
            "group_B_identical_night_probability_for_all_species":B,
            "species_composition_weights":witness,
            "actual_two_study_areas_or_camera_station_membership_measured":False,
            "expected_counts_only_not_real_stations_or_true_individuals":True,
            "possible_even_with_perfect_equal_camera_q":True,
        },
        "published_period_hours_are_not_original_camera_operation_hours":True,
        "original_frozen_41_mirror_pairs_observed":False,
        "per_camera_robust_species_temporal_differentiation_identified":False,
        "consequential_uncertainty_or_new_p_calculated":False,
        "latent_activity_or_competition_causality_claimed":False
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--offline-supp3-zip", type=Path,
                   help="Published Zenodo Supplement 3 ZIP; NOT the EcoBank original ZIP")
    args = p.parse_args()
    archive = args.offline_supp3_zip.read_bytes() if args.offline_supp3_zip else download()
    result = inspect(
        json.loads(CONTRACT.read_text()),
        json.loads(SOURCE_CONTRACT.read_text()),
        archive)
    print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))


if __name__ == "__main__":
    main()
