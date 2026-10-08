"""Pre-result source-free counterfactual geometry placebo validations."""
import json
from pathlib import Path
import numpy as np
import pytest

from odsp.uljin_geometry_neutral_paired_placebo_v1 import (
    three_same_event_frames,run_paired_geometry_placebo_panel,
)
from odsp.uljin_finite_sample_clock_alias_selection_v0 import (
    PROFILES,SEED,inverse_cdf_table,event_count_frames,geometry_for_pairs,
)
from odsp.uljin_photoperiod_mirror_design_v0 import (
    generate_preoutcome_2022_mirror_calendar,
)

ROOT=Path(__file__).resolve().parents[1]
read=lambda name:json.loads((ROOT/name).read_text())
CAL=read("ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json")
V0=read("ULJIN_FINITE_SAMPLE_CLOCK_ALIAS_SELECTION_V0_CONTRACT.json")
LEDGER=read("ULJIN_FINITE_SAMPLE_CLOCK_ALIAS_SELECTION_V0_FIRST_RESULT_LEDGER.json")
PLAN=read("ULJIN_GEOMETRY_NEUTRAL_PAIRED_PLACEBO_V1_CONTRACT.json")


def test_same_exact_latent_events_and_original_v0_replay_of_frames():
    dates=generate_preoutcome_2022_mirror_calendar(CAL)["matched_dates"]
    geometry=geometry_for_pairs(dates)
    cdf,grid=inverse_cdf_table(PROFILES[2])
    seed=np.random.SeedSequence([SEED,2,2,0])
    a,p,s,n=three_same_event_frames(
        np.random.default_rng(seed),46230,geometry,cdf,grid)
    old_a,old_s,old_n=event_count_frames(
        np.random.default_rng(seed),46230,geometry,cdf,grid)
    assert n==old_n
    assert np.array_equal(a,old_a)
    assert np.array_equal(s,old_s)
    assert np.array_equal(a.sum(axis=2),p.sum(axis=2))
    assert np.array_equal(p.sum(axis=2),s.sum(axis=2))
    assert np.any(a!=p)


def test_source_free_control_panel_preflight_deterministic():
    first=run_paired_geometry_placebo_panel(
        CAL,V0,LEDGER,PLAN,_test_world_count=2)
    second=run_paired_geometry_placebo_panel(
        CAL,V0,LEDGER,PLAN,_test_world_count=2)
    assert first==second
    assert first["case_count"]==9
    assert first["worlds_per_case"]==2
    assert not first["real_wildlife_event_rows_read"]
    for c in first["cases"]:
        assert -1<=c["paired_excess_clock_only_frequency"]<=1
        assert c["paired_excess_monte_carlo_standard_error"]>=0


def test_predeclared_frozen_counterfactual_must_not_change():
    bad=json.loads(json.dumps(PLAN))
    bad["total_expected_event_counts"][1]=5000
    with pytest.raises(ValueError,match="contract"):
        run_paired_geometry_placebo_panel(
            CAL,V0,LEDGER,bad,_test_world_count=1)

    missing=json.loads(json.dumps(LEDGER))
    missing["first_ci_head_sha"]="unverified"
    with pytest.raises(ValueError,match="contract"):
        run_paired_geometry_placebo_panel(
            CAL,V0,missing,PLAN,_test_world_count=1)
