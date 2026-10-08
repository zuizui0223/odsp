"""Outcome-free scientific falsification tests for time coordinates and detection.

Two known-truth worlds explicitly favor opposing invariance hypotheses.
Context-conditional UNRESTRICTED models are provably equivalent through the
Jacobian, so same parameter count on binned features alone is inadequate.
No RI animal records, empirical score searches, or model requalification.
"""
from __future__ import annotations

from datetime import date
import json

import numpy as np
import pytest

from odsp.ri_temporal_coordinate_equivalence_synthetic_v0 import (
    AstronomicalContext, solar_phase_and_clock_jacobian,
    clock_time_and_inverse_jacobian, von_mises_hour_density,
    clock_density_from_solar, solar_density_from_clock,
    time_grid, synthetic_population_coordinate_test,
    detected_density_from_activity_and_effort,
    effort_reconstructing_arbitrary_detected_density,
)

def contexts():
    return (
        AstronomicalContext.from_day("winter",date(2022,12,21),41.5,-71.5),
        AstronomicalContext.from_day("summer",date(2022,6,21),41.5,-71.5),
    )


def frozen():
    from pathlib import Path
    path=(Path(__file__).resolve().parents[1]/
          "RI_TEMPORAL_COORDINATE_EQUIVALENCE_SYNTHETIC_V0_CONTRACT.json")
    return json.loads(path.read_text(encoding="utf-8"))


def test_solar_to_clock_and_clock_to_solar_are_exact_inverses_with_jacobian():
    grid,_=time_grid(24000)
    for context in contexts():
        phase,jac=solar_phase_and_clock_jacobian(grid,context)
        clock,inverse=clock_time_and_inverse_jacobian(phase,context)
        # Correct periodic circular distance, including the midnight wrap.
        separation=((clock-grid+12.0)%24.0)-12.0
        assert np.max(np.abs(separation))<1e-11
        assert np.allclose(jac*inverse,1,rtol=1e-12,atol=1e-12)
        assert np.min(jac)>0
        assert np.max(phase)<24.


def test_unrestricted_context_specific_density_coordinate_equivalence_pointwise():
    t,_=time_grid(24000)
    f=lambda hours: von_mises_hour_density(
        hours,peak_hour=17.4,concentration=5.0
    )
    for context in contexts():
        phi,J=solar_phase_and_clock_jacobian(t,context)
        g=lambda phase:solar_density_from_clock(phase,context,f)
        f_clock=f(t)
        f_reconstructed=clock_density_from_solar(t,context,g)
        assert np.allclose(f_reconstructed,f_clock,rtol=1e-11,atol=1e-12)
        # A positive phase-density mass stays properly normalized when
        # evaluated in the SAME local civil time outcome space.
        assert abs(np.mean(f_reconstructed)*24.-1.0)<.002


def test_winter_summer_solar_truth_and_clock_truth_both_win_when_correctly_specified():
    out=synthetic_population_coordinate_test(frozen())
    assert out["status"]=="KNOWN_TRUTH_SYNTHETIC_COORDINATE_INVARIANCE"
    for world in ("known_solar_invariant_truth","known_clock_invariant_truth"):
        info=out[world]
        assert info["equal_context_mean_advantage"]>0.001
        for name in ("winter","summer"):
            assert info[
                "expected_nats_advantage_of_correct_solar_over_optimal_pooled_clock"
                if world.startswith("known_solar") else
                "expected_nats_advantage_of_correct_clock_over_optimal_pooled_solar"
            ][name]>0
    assert all(abs(mass-1.0)<.002
               for mass in out["numerical_density_mass"].values())
    assert out["context_unrestricted_density_families_equivalent"] is True
    assert out["solar_histogram_clock_bin_convex_hull_limit_imposed"] is False
    assert out["real_RI_wildlife_detection_rows_accessed"] is False
    assert out["previous_v2_ecological_result_reclassified"] is False
    json.dumps(out,allow_nan=False)


def test_correct_jacobian_is_essential_to_common_clock_density_score():
    grid,dt=time_grid(24000)
    s=contexts()[0]
    phase,J=solar_phase_and_clock_jacobian(grid,s)
    g=von_mises_hour_density(phase,peak_hour=7.5,concentration=2.2)
    proper=g*J
    # Absent the change-of-measure factor, solar density values at phase
    # points DO NOT generally normalize under the civil-time measure.
    assert abs(float(dt*np.sum(proper))-1)<.002
    assert abs(float(dt*np.sum(g))-1)>.005


def test_detection_effort_can_exactly_alias_incompatible_animal_activity():
    grid,dt=time_grid(24000)
    observed=von_mises_hour_density(
        grid,peak_hour=6.,concentration=2.8
    )
    activity_one=von_mises_hour_density(
        grid,peak_hour=6.,concentration=2.0
    )
    activity_two=von_mises_hour_density(
        grid,peak_hour=17.,concentration=2.0
    )
    effort1=effort_reconstructing_arbitrary_detected_density(
        observed,activity_one
    )
    effort2=effort_reconstructing_arbitrary_detected_density(
        observed,activity_two
    )
    assert np.min(effort1)>0 and np.max(effort1)<=.5000001
    assert np.min(effort2)>0 and np.max(effort2)<=.5000001
    d1=detected_density_from_activity_and_effort(activity_one,effort1,dt)
    d2=detected_density_from_activity_and_effort(activity_two,effort2,dt)
    assert np.allclose(d1,observed,rtol=1e-12,atol=1e-14)
    assert np.allclose(d2,observed,rtol=1e-12,atol=1e-14)
    assert not np.allclose(activity_one,activity_two,rtol=.01,atol=.01)
    assert not np.allclose(effort1,effort2,rtol=.01,atol=.01)


def test_unfrozen_grid_and_incorrect_coordinate_values_are_rejected():
    plan=frozen()
    plan["synthetic_plan"]["numerical_midpoint_grid_points"]=12000
    with pytest.raises(ValueError,match="frozen synthetic"):
        synthetic_population_coordinate_test(plan)
    for context in contexts():
        with pytest.raises(ValueError,match="hours"):
            solar_phase_and_clock_jacobian(np.array([24.]),context)
        with pytest.raises(ValueError,match="hours"):
            clock_time_and_inverse_jacobian(np.array([-1.]),context)
    with pytest.raises(ValueError,match="exposure"):
        detected_density_from_activity_and_effort(
            np.ones(10),np.zeros(10),.1
        )
