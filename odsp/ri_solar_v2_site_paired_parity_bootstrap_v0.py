"""Post-result original-site paired bootstrap for season-aware solar-vs-clock.

This is a NEW POST-OUTCOME exploratory uncertainty diagnostic. It does not
change the original v2 source/model/target or the original negative outcome.
We first replay the exact original N=19,916 scored detections, 43 heldout
sites, winter/summer S-C means AND their original 5% bootstrap limits.
Only if all guards pass do we compute the new row-wise identity:
  (solar-clock)+(solar_season-solar)-(clock_season-clock),
then average per site x season-year, then years, then sites.

Each bootstrap draw assigns ONE exponential multiplier per entire
physical site, using the original seed/draw count. The SAME site
multipliers are used across all contrast types and both seasons.
This preserves the covariance the first aggregated receipt omitted.
Percentile intervals here are explicitly post hoc and not qualified
confirmatory coverage guarantees, especially for selected spatial sites.
"""
from __future__ import annotations

from collections import defaultdict, Counter
import hashlib
import math
from typing import Any,Mapping,Sequence

import numpy as np

from .ri_solar_clock_transfer_v0 import (
    DielEvent,fit_species_profiles,score_new_site_future_year,
    site_is_sealed,summarize_site_level_transfer,
)
from .ri_solar_clock_yearseason_v2 import (
    v2_events_from_two_tables,_validate_contract as validate_v2,
)
from .ri_solar_source_v0 import _member_zip_csv

VERSION="ri_solar_v2_postoutcome_paired_site_parity_bootstrap_v0"
SCORING_KEYS=(
    "solar_over_clock",
    "solar_season_over_solar",
    "clock_season_over_clock",
)


def _plan_checked(plan:Mapping[str,object])->None:
    if (
        plan.get("schema_version")!=1
        or plan.get("analysis_id")!=
            "ri_solar_v2_site_paired_season_parity_bootstrap_v0"
        or plan.get("status")!=
            "POST_OUTCOME_EXPLORATORY_COVARIANCE_RECOVERY_NOT_PRIMARY"
    ):
        raise ValueError("unknown frozen paired-site source/estimator contract")
    ref=plan.get("first_original",{})
    if (
        ref.get("scored_detection_events")!=19916
        or ref.get("distinct_heldout_physical_sites")!=43
        or ref.get("first_scientific_status")!=
            "EXPLORATORY_NOT_SUPPORTED_OR_UNAVAILABLE"
    ):
        raise ValueError("original RI first outcome identity differs")
    boot=plan.get("bootstrap",{})
    if (
        boot.get("replicates")!=2000
        or boot.get("seed")!=2026100803
        or boot.get("percentiles_two_sided")!=[.025,.975]
        or boot.get("original_pooled_component_bootstrap_lower_quantile")!=.05
        or boot.get("original_pooled_bootstrap_match_tolerance")!=1e-10
        or boot.get("no_retroactive_confirmatory_significance_claim") is not True
    ):
        raise ValueError("post-outcome frozen paired bootstrap changed")
    if (
        plan.get("new_descriptive_target",{}).get(
            "no_favorable_species_or_site_filtering"
        ) is not True
    ):
        raise ValueError("matched or selected sites disallowed")


def original_all_site_score_rows(
    source_archive:bytes,
    original_v2_contract:Mapping[str,object],
    postoutcome_plan:Mapping[str,object],
)->tuple[list[tuple[DielEvent,dict[str,float]]],dict[str,Any]]:
    """Rerun the SAME original ecological model; don't recode/screen it."""
    _plan_checked(postoutcome_plan)
    validate_v2(original_v2_contract)
    members=_member_zip_csv(source_archive)
    events,source_audit=v2_events_from_two_tables(
        members["RI_CameraSurvey_Deployments.csv"],
        members["RI_CameraSurvey_Detections.csv"],
        original_v2_contract,
    )
    train=[
        e for e in events if e.season_year<=2021
        and not site_is_sealed(e.site_id)
    ]
    future=[
        e for e in events if e.season_year>=2022
        and site_is_sealed(e.site_id)
    ]
    models,train_audit=fit_species_profiles(train)
    scores=[
        (e,score_new_site_future_year(e,models[e.species]))
        for e in future if e.species in models
    ]
    reference=postoutcome_plan["first_original"]
    if len(scores)!=reference["scored_detection_events"]:
        raise ValueError("original first scored detection count not recovered")
    if len({e.site_id for e,_ in scores})!=reference["distinct_heldout_physical_sites"]:
        raise ValueError("original first heldout physical site count not recovered")
    observed=summarize_site_level_transfer(scores)
    atol=postoutcome_plan["bootstrap"]["original_pooled_bootstrap_match_tolerance"]
    for season in ("winter","summer"):
        original=observed["season_groups"][season]
        expected_mean=reference[f"{season}_solar_minus_clock"]
        expected_lower=reference[f"{season}_pooled_solar_95_lower"]
        actual=original["metrics"]["solar_over_clock"]
        if abs(actual["mean"]-expected_mean)>atol:
            raise ValueError(f"original {season} heldout solar/clock mean not replayed")
        if abs(actual["one_sided_95_percent_cluster_bootstrap_lower"]-expected_lower)>atol:
            raise ValueError(f"original {season} 5% site-bootstrap lower bound not replayed")
    return scores,{
        "first_scored_detection_count":len(scores),
        "first_heldout_site_count":len({e.site_id for e,_ in scores}),
        "original_source_audit":{
            "source_image_rows":source_audit["source_detection_image_row_count"],
            "retained_original_30min_events":source_audit[
                "detection_filter_counts"
            ].get("retained_independent_30min_detection_events"),
        },
        "train_only_species_count":len(models),
        "original_means_and_lower_bootstrap_limits_replayed_exactly":True,
    }


def paired_site_season_parity_interval(
    scores:Sequence[tuple[DielEvent,dict[str,float]]],
    plan:Mapping[str,object],
)->dict[str,Any]:
    """Compute paired *site* uncertainty for new post-result composite mean."""
    _plan_checked(plan)
    # Site×season×year aggregation before any reweighting or new subset.
    site_year:dict[tuple[str,str,int],dict[str,list[float]]]=defaultdict(
        lambda:defaultdict(list)
    )
    for event,item in scores:
        if not site_is_sealed(event.site_id) or event.season_year not in (2022,2023):
            raise ValueError("new inference source is not an original heldout site/year")
        for key in SCORING_KEYS:
            value=item.get(key)
            if not isinstance(value,(float,int)) or not math.isfinite(float(value)):
                raise ValueError(f"invalid original scoring cell {key}")
            site_year[event.site_id,event.season,event.season_year][key].append(
                float(value)
            )
    site_season:dict[tuple[str,str],dict[str,list[float]]]=defaultdict(
        lambda:defaultdict(list)
    )
    for (site,season,_year),group in site_year.items():
        for key in SCORING_KEYS:
            site_season[site,season][key].append(float(np.mean(group[key])))
    site_data={}
    for key,components in site_season.items():
        values={comp:float(np.mean(year_values))
                for comp,year_values in components.items()}
        values["solar_season_minus_clock_season"]=(
            values["solar_over_clock"]
            +values["solar_season_over_solar"]
            -values["clock_season_over_clock"]
        )
        site_data[key]=values
    all_sites=sorted({site for site,season in site_data})
    ref=plan["first_original"]
    if len(all_sites)!=ref["distinct_heldout_physical_sites"]:
        raise ValueError("changed original heldout site support")
    rng=np.random.default_rng(plan["bootstrap"]["seed"])
    site_weights=rng.exponential(
        1.0,size=(plan["bootstrap"]["replicates"],len(all_sites))
    )
    indices={site:i for i,site in enumerate(all_sites)}
    output={}
    for season in ("winter","summer"):
        season_sites=sorted(site for site,s in site_data if s==season)
        if len(season_sites)!=43:
            raise ValueError("original season physical site roster changed")
        x=np.asarray([
            site_data[site,season]["solar_season_minus_clock_season"]
            for site in season_sites
        ],dtype=float)
        pooled=np.asarray([
            site_data[site,season]["solar_over_clock"]
            for site in season_sites
        ],dtype=float)
        # Same physical-site exponential multipliers across ALL seasons
        # and all contrasts; never combine marginal interval endpoints.
        weights=site_weights[:,[indices[site] for site in season_sites]]
        denominator=weights.sum(axis=1)
        simulated=(weights@x)/denominator
        simulated_pooled=(weights@pooled)/denominator
        if (
            abs(float(np.mean(pooled))-ref[f"{season}_solar_minus_clock"])
            >plan["bootstrap"]["original_pooled_bootstrap_match_tolerance"]
            or abs(
                float(np.quantile(simulated_pooled,.05))
                -ref[f"{season}_pooled_solar_95_lower"]
            )>plan["bootstrap"]["original_pooled_bootstrap_match_tolerance"]
        ):
            raise ValueError("original same-site mean or bootstrap draw geometry changed")
        lower,upper=np.quantile(
            simulated,plan["bootstrap"]["percentiles_two_sided"]
        )
        output[season]={
            "physical_site_count":len(season_sites),
            "original_pooled_solar_minus_clock_mean":
                float(np.mean(pooled)),
            "conditional_solar_season_minus_clock_season_mean":
                float(np.mean(x)),
            "paired_site_multiplier_bootstrap_95_percentile_lower":float(lower),
            "paired_site_multiplier_bootstrap_95_percentile_upper":float(upper),
            "interval_excludes_zero":bool(upper<0 or lower>0),
            "new_interval_is_postoutcome_exploratory_only":True,
            "independent_spatial_sampling_and_coverage_verified":False,
        }
    return {
        "schema_version":1,
        "method_version":VERSION,
        "status":"POST_OUTCOME_SITE_PAIRED_PARITY_BOOTSTRAP_ONLY",
        "original_primary_both_seasons_solar_superiority_supported":False,
        "original_result_exactly_replayed_before_new_interval":True,
        "scored_events":len(scores),
        "original_heldout_sites":len(all_sites),
        "season_groups":output,
        "bootstrap_draws":plan["bootstrap"]["replicates"],
        "bootstrap_seed":plan["bootstrap"]["seed"],
        "bootstrap_random_sites_reused_across_seasons":True,
        "all_confirmatory_claims_prohibited":True,
        "ecological_causal_photoperiod_mechanism_identified":False,
        "original_ODSP_statistical_routes_reclassified":False,
    }
