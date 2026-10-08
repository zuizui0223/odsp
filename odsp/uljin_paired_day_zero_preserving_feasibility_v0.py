"""Public-aggregate-only sparsity and zero-count support for Uljin date mirrors.

This is a HYPOTHETICAL DESIGN MODEL, not observed animal source data.
The 4,623 published events and 29,850 functional camera nights provide
ONE pooled historical rate. Assuming uniform iid Poisson events across
all 82 stations, dates and four equally abundant species yields a
conditional expected number of matched positive detections on BOTH
dates at the same station and species. That estimate is NOT an empirical
eligibility count and NOT a statistical upper bound under heterogeneity.

More importantly, a camera-hour-exposure-adjusted POISSON log score
uses zero-detection cells as real information when a validated
station-hour operation log establishes positive exposure. Missing
exposure is never converted to an observed zero. Every competing
candidate MUST score the SAME civil-clock count-bin response.

No original ZIP, wildlife detection rows, station IDs, camera times,
or actual species labels are opened by this module.
"""
from __future__ import annotations

from dataclasses import asdict,dataclass
import math
from typing import Any,Mapping,Sequence

ID="odsp-uljin-outcome-free-paired-day-detection-sparsity-plan-v0"
EVENTS=4623
NIGHTS=29850
STATIONS=82
SPECIES=4
PAIRS=41
CLOCK_BINS=6


def _plan_guard(plan:Mapping[str,object])->None:
    if (not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=ID
        or plan.get("status_result")!=
            "HYPOTHETICAL_POWER_AND_ZERO_EXPOSURE_DESIGN_NOT_ECOLOGY"):
        raise ValueError("unrecognized source-free Uljin sparsity design")
    src=plan.get("source_provenance",{})
    expected={
        "published_independent_detection_events":EVENTS,
        "published_functional_camera_nights":NIGHTS,
        "published_camera_stations":STATIONS,
        "published_focal_species":SPECIES,
        "original_calendar_pairs":PAIRS,
        "publishing_time_counts_not_source_outcome_rows":True,
    }
    if not isinstance(src,Mapping) or any(src.get(k)!=v for k,v in expected.items()):
        raise ValueError("published source-wide aggregate sizes differ from frozen design")
    zero=plan.get("zero_preserving_design",{})
    if not isinstance(zero,Mapping) or any(
        zero.get(k) is not True for k in (
        "zero_with_positive_exposure_must_contribute_to_predictive_log_score",
        "count_without_exposure_must_fail_closed",
        "zero_exposure_zero_count_is_uninformative_not_a_photographic_nondetection",
        "no_species_based_station_admission_after_outcomes",
        "no_pair_reselection_after_animal_observations")
    ) or zero.get("minimum_per_bin_functional_hours")!=3:
        raise ValueError("zero-support frame rules differ from frozen science design")


def _binomial_tail_at_least(n:int,p:float,k:int)->float:
    """Exact iid scenario Binomial survival; NOT a real data p-value."""
    if not 0<=p<=1 or k<0 or n<0:
        raise ValueError("bad hypothetical Bernoulli parameters")
    return min(1.,max(0.,math.fsum(
        math.comb(n,i)*p**i*(1-p)**(n-i)
        for i in range(k,n+1)
    )))


def hypothetical_station_species_pair_feasibility(
    plan:Mapping[str,object],
)->dict[str,Any]:
    """Published totals + explicitly idealized Poisson exchangeability."""
    _plan_guard(plan)
    lambda_all=EVENTS/NIGHTS
    lambda_taxon=lambda_all/SPECIES
    detection_at_least_one=1-math.exp(-lambda_taxon)
    double_detection=detection_at_least_one**2
    trials=STATIONS*PAIRS*SPECIES
    expected_matched_event_pairs=trials*double_detection
    per_station_species_at_least_one_of_41=1-(1-double_detection)**PAIRS
    expected_distinct_station_species_with_at_least_one_pair=(
        STATIONS*SPECIES*per_station_species_at_least_one_of_41
    )
    expected_station_support_per_species=(
        STATIONS*per_station_species_at_least_one_of_41
    )
    return {
        "schema_version":1,
        "method":"uljin_published_aggregate_homogeneous_poisson_sparsity_v0",
        "status":"HYPOTHETICAL_RATE_SCENARIO_NEVER_ACTUAL_ULJIN_SOURCE_SUPPORT",
        "published_source_events":EVENTS,
        "published_source_camera_nights":NIGHTS,
        "assumed_all_four_taxa_equal_rate":True,
        "all_species_pooled_events_per_functional_camera_night":lambda_all,
        "hypothetical_each_species_events_per_camera_night":lambda_taxon,
        "hypothetical_detection_probability_per_fully_operational_night_per_species":detection_at_least_one,
        "hypothetical_both_dates_detected_same_station_species_probability":double_detection,
        "hypothetical_station_species_date_pair_trials":trials,
        "hypothetical_expected_station_species_date_pairs_with_both_days_detected":expected_matched_event_pairs,
        "hypothetical_expected_station_species_combinations_with_any_matched_pair":expected_distinct_station_species_with_at_least_one_pair,
        "hypothetical_expected_distinct_stations_per_species_with_any_matched_pair":expected_station_support_per_species,
        "hypothetical_probability_at_least_eight_of_82_stations_have_any_matched_pair_for_one_species":_binomial_tail_at_least(
            STATIONS,per_station_species_at_least_one_of_41,8
        ),
        "this_is_not_empirical_matched_site_taxon_observation":True,
        "rate_homogeneity_and_station_iid_verified":False,
        "source_event_counts_by_taxon_available_for_this_calculation":False,
        "real_camera_hour_eligibility_observed":False,
        "zero_detection_cells_are_missing_when_camera_not_running":True,
        "real_animal_records_opened":False,
        "earlier_ODSP_ecological_results_reclassified":False,
    }


def fixed_clock_bin_poisson_log_score(
    counts:Sequence[int],
    exposure_hours:Sequence[float],
    predicted_rate_per_active_hour:Sequence[float],
)->float:
    """Proper log P(Y=n | Poisson(exposure_hours × rate)).

    All three arrays must refer to the SAME six original civil-clock
    bins for ALL candidate models. An operational observation with
    positive exposure and zero detections contributes -exposure*rate.
    The value 0 exposure/0 detections contributes nothing; positive
    detection with zero exposure is impossible and FAILS CLOSED.
    """
    if (
        len(counts)!=CLOCK_BINS or
        len(exposure_hours)!=CLOCK_BINS or
        len(predicted_rate_per_active_hour)!=CLOCK_BINS
    ):
        raise ValueError("requires exactly six common 4-hour clock bins")
    total=0.
    for n,e,r in zip(counts,exposure_hours,predicted_rate_per_active_hour):
        if isinstance(n,bool) or not isinstance(n,int) or n<0:
            raise ValueError("counts must be nonnegative integers")
        if (
            isinstance(e,bool) or not isinstance(e,(int,float))
            or not math.isfinite(float(e)) or not 0<=e<=4
            or isinstance(r,bool) or not isinstance(r,(int,float))
            or not math.isfinite(float(r)) or r<=0
        ):
            raise ValueError("invalid nonnegative clock-bin uptime or positive rate")
        mu=float(e)*float(r)
        if mu==0:
            if n:
                raise ValueError("observed detection with no validated operating exposure")
            continue
        total+=n*math.log(mu)-mu-math.lgamma(n+1)
    return total
