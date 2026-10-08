"""Four taxon-specific hypothetical mirror-day detection sparsity scenarios.

PUBLIC PAPER AGGREGATES ONLY: all 4,623 source detections (2317/814/
808/684) and 29,850 camera-nights come from the original article,
not opened wildlife event data. With HOMOGENEOUS iid Poisson station-
date detections, the expected SAME species at SAME station detected
on BOTH dates of an original 41-day pair can be computed exactly.

This is not empirical pair support, not a conservative bound under
spatial/rate heterogeneity, and not an evaluation of clock/solar biology.
It illustrates why selecting only doubly observed station-date pairs
is likely to bias against less-recorded species. Zero events at
verified positive operational exposure must remain in a future model.
"""
from __future__ import annotations

import math
from typing import Mapping,Any

ID="odsp-uljin-post-v0-published-taxon-rate-feasibility-v1"
TAXA={
    "Naemorhedus caudatus":2317,
    "Hydropotes inermis":814,
    "Capreolus pygargus":808,
    "Sus scrofa":684,
}


def published_taxon_rate_sparsity_scenario(
    plan:Mapping[str,object],
)->dict[str,Any]:
    if (
        not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=ID
        or plan.get("status")!=
            "PUBLICATION_AGGREGATE_ONLY_POST_INITIAL_EQUAL_TAXON_SCENARIO"
        or plan.get("predeclared_four_species_total_counts")!=TAXA
        or plan.get("published_functional_camera_nights")!=29850
        or plan.get("published_stations")!=82
        or plan.get("original_frozen_astronomical_date_pairs")!=41
        or plan.get("all_species_event_total_expected")!=4623
        or plan.get("actual_source_station_species_event_distribution_unobserved") is not True
        or plan.get("no_original_ecology_or_qualified_ODSP_route_promoted") is not True
    ):
        raise ValueError("published taxon-rate source-free design identity changed")
    if sum(TAXA.values())!=4623:
        raise ValueError("original four article species count sum changed")
    rows=[]
    for taxon,events in TAXA.items():
        lam=events/29850
        p_night=-math.expm1(-lam)
        p_pair=p_night*p_night
        p_site_ever=-math.expm1(41*math.log1p(-p_pair))
        rows.append({
            "taxon":taxon,
            "article_total_independent_events":events,
            "hypothetical_pooled_events_per_functional_camera_night":lam,
            "homogeneous_iid_Poisson_probability_at_least_one_detection_per_functional_night":p_night,
            "homogeneous_iid_Poisson_probability_detected_both_mirror_dates":p_pair,
            "expected_station_taxon_date_pairs_with_both_dates_detected":82*41*p_pair,
            "expected_distinct_stations_for_this_taxon_with_at_least_one_mirror_pair_both_dates_detected":82*p_site_ever,
        })
    return {
        "schema_version":1,
        "method":"uljin_source_free_species_heterogeneous_poisson_feasibility_v1",
        "status":"HYPOTHETICAL_SPECIES_LEVEL_SUPPORT_NOT_FIELD_RESULT",
        "source_article":"10.3897/BDJ.14.e191556",
        "original_41_matched_calendar_dates_changed":False,
        "assumes_equal_site_date_detection_intensity_within_each_taxon":True,
        "uses_published_global_taxon_totals_not_source_event_rows":True,
        "source_operation_hourly_coverage_verified":False,
        "real_station_or_date_eligibility_verified":False,
        "published_species_scenarios":rows,
        "sum_hypothetical_matched_station_species_date_pairs":sum(
            row["expected_station_taxon_date_pairs_with_both_dates_detected"]
            for row in rows
        ),
        "selection_bias_from_only_doubly_observed_station_day_species_cells_possible":True,
        "independent_spatial_sampling_or_Poisson_process_validated":False,
        "no_original_primary_ecological_route_changed":True,
        "new_wildlife_mechanism_claimed":False,
    }
