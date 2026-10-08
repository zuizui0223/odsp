"""No camera source records: known-truth homogeneous Poisson feasibility."""
from __future__ import annotations
import json
import math
from pathlib import Path

import pytest

from odsp.uljin_paired_day_zero_preserving_feasibility_v0 import (
    hypothetical_station_species_pair_feasibility,
    fixed_clock_bin_poisson_log_score,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads(
    (ROOT/"ULJIN_PAIRED_DAY_ZERO_PRESERVING_FEASIBILITY_V0_CONTRACT.json").read_text()
)


def test_published_aggregates_only_support_a_conditional_sparsity_scenario():
    r=hypothetical_station_species_pair_feasibility(PLAN)
    assert r["hypothetical_station_species_date_pair_trials"]==41*82*4
    assert r["all_species_pooled_events_per_functional_camera_night"]==pytest.approx(4623/29850)
    assert r["hypothetical_each_species_events_per_camera_night"]==pytest.approx(4623/29850/4)
    assert r["hypothetical_expected_station_species_date_pairs_with_both_days_detected"]==pytest.approx(
        19.397055886240327
    )
    assert 0<r["hypothetical_expected_distinct_stations_per_species_with_any_matched_pair"]<8
    assert r["rate_homogeneity_and_station_iid_verified"] is False
    assert r["this_is_not_empirical_matched_site_taxon_observation"] is True
    assert r["real_camera_hour_eligibility_observed"] is False
    assert r["real_animal_records_opened"] is False
    assert r["earlier_ODSP_ecological_results_reclassified"] is False
    json.dumps(r,allow_nan=False)


def test_validated_positive_camera_effort_with_zero_detection_informs_log_score():
    counts=[0,0,0,0,0,0]
    exposure=[4.,4.,4.,4.,4.,4.]
    low_rate=[.01]*6
    high_rate=[.02]*6
    low=fixed_clock_bin_poisson_log_score(counts,exposure,low_rate)
    high=fixed_clock_bin_poisson_log_score(counts,exposure,high_rate)
    assert low==pytest.approx(-.24)
    assert high==pytest.approx(-.48)
    assert low>high
    assert fixed_clock_bin_poisson_log_score(counts,[0.]*6,low_rate)==0.


def test_no_operational_exposure_with_detected_event_fails_closed():
    with pytest.raises(ValueError,match="no validated operating exposure"):
        fixed_clock_bin_poisson_log_score(
            [1,0,0,0,0,0],[0.]*6,[.01]*6
        )


def test_same_clock_partition_is_necessary_for_comparable_log_scores():
    with pytest.raises(ValueError,match="six common"):
        fixed_clock_bin_poisson_log_score([0]*6,[4.]*5,[.1]*6)
    with pytest.raises(ValueError,match="nonnegative integers"):
        fixed_clock_bin_poisson_log_score([False]+[0]*5,[4.]*6,[.1]*6)
    with pytest.raises(ValueError,match="invalid nonnegative"):
        fixed_clock_bin_poisson_log_score([0]*6,[5.]+[4.]*5,[.1]*6)
    with pytest.raises(ValueError,match="invalid nonnegative"):
        fixed_clock_bin_poisson_log_score([0]*6,[4.]*6,[0.]+[.1]*5)


def test_fixed_source_total_and_zero_inclusion_gates_cannot_be_retuned():
    plan=json.loads(json.dumps(PLAN))
    plan["source_provenance"]["published_independent_detection_events"]=5000
    with pytest.raises(ValueError,match="source-wide aggregate"):
        hypothetical_station_species_pair_feasibility(plan)
    plan=json.loads(json.dumps(PLAN))
    plan["zero_preserving_design"]["zero_with_positive_exposure_must_contribute_to_predictive_log_score"]=False
    with pytest.raises(ValueError,match="zero-support"):
        hypothetical_station_species_pair_feasibility(plan)


def test_zero_exposure_vs_zero_count_is_not_same_as_fully_operating_zero():
    rate=[.015]*6
    covered=fixed_clock_bin_poisson_log_score([0]*6,[3.]*6,rate)
    unknown=fixed_clock_bin_poisson_log_score([0]*6,[0.]*6,rate)
    assert covered==pytest.approx(-.27)
    assert unknown==0.
    assert covered<unknown
