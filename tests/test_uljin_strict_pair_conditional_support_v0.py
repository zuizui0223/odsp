"""Independent exact occupancy mathematical and scientific-status guardrails."""
import json
import math
from pathlib import Path
from odsp.uljin_strict_pair_conditional_support_v0 import (
    expected_both_branches, expected_at_least_two_any_branch,
    run_strict_pair_support_screen, G,
)
import pytest

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads(
    (ROOT/"ULJIN_STRICT_PAIR_CONDITIONAL_SUPPORT_V0_CONTRACT.json").read_text())


def test_exact_finite_multinomial_n2_one_group_branch_allocation():
    # Two iid events, both in the only group, independently choose A/D.
    assert expected_both_branches(2,1.,1)==pytest.approx(.5,abs=1e-12)
    assert expected_at_least_two_any_branch(2,1.,1)==pytest.approx(1)
    assert expected_both_branches(1,1.,1)==0
    assert expected_at_least_two_any_branch(1,1.,1)==0


def test_small_n_exact_enumeration_exclusive_cases():
    # N=2, G=2, all events in candidate pairs:
    # probability both A/D in SAME group is 2*(1/2)^2*(1/2)=1/4;
    # hence expected number of both-branch groups is 0.25.
    assert expected_both_branches(2,1.,2)==pytest.approx(.25,abs=1e-12)
    assert expected_at_least_two_any_branch(2,1.,2)==pytest.approx(.5,abs=1e-12)


def test_count_conservation_bounds_and_monotone_scenario_retention():
    for n in [0,1,2,5,684,814,2317,4623]:
        v=[expected_both_branches(n,f,G) for f in [0.,.1,.25,1.]]
        assert all(0<=x<=min(G,n//2) for x in v)
        assert v==sorted(v)
        for f in [0.,.1,.25,1.]:
            assert expected_both_branches(n,f,G)<=(
                expected_at_least_two_any_branch(n,f,G)+1e-8
            )


def test_full_published_event_scenario_and_taxon_separation():
    out=run_strict_pair_support_screen(PLAN)
    assert out["published_event_total_pooled"]==4623
    assert out["nominal_site_pair_group_count"]==82*41
    assert len(out["cases"])==15
    counts={c["taxon"]:c["full_year_published_event_count"]
            for c in out["cases"]}
    assert counts["goral"]==2317
    assert counts["water_deer"]==814
    assert counts["roe_deer"]==808
    assert counts["wild_boar"]==684
    assert not out["actual_source_events_opened"]
    assert out["single_branch_observations_still_inform_pooled_conditional_poisson"]
    assert out["this_is_not_a_pooled_conditional_poisson_power_bound"]
    assert all(c["real_observed_both_branch_groups_known"] is False
               for c in out["cases"])
    json.dumps(out,allow_nan=False)


def test_contract_mutation_and_invalid_numeric_inputs_fail_closed():
    altered=json.loads(json.dumps(PLAN))
    altered["selected_day_event_retention_scenarios"]=[1.,.3,.1]
    with pytest.raises(ValueError,match="contract"):
        run_strict_pair_support_screen(altered)
    for args in [(-1,1.,G),(1,1.1,G),(2,-.1,G),(2,1.,0),
                 (2,float("nan"),G)]:
        with pytest.raises(ValueError):
            expected_both_branches(*args)
