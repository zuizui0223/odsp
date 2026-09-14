from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from odsp.transfer_ceiling_operating_characteristics import (
    GENERATOR_VERSION,
    _step_noise,
    run_transfer_ceiling_operating_characteristics,
)


ROOT = Path(__file__).resolve().parents[1]


def test_mixed_truth_generator_is_seed_deterministic():
    first = _step_noise(
        np.random.default_rng(20260915),
        blocks=12,
        group_count=3,
        rho=0.4,
        sigma=0.2,
        distribution="normal",
    )
    second = _step_noise(
        np.random.default_rng(20260915),
        blocks=12,
        group_count=3,
        rho=0.4,
        sigma=0.2,
        distribution="normal",
    )
    assert np.array_equal(first, second)
    assert first.shape == (12, 3, 2)


def test_small_operating_characteristics_run_is_reproducible_and_exhaustive():
    first = run_transfer_ceiling_operating_characteristics(
        simulations_per_scenario=100,
        bootstrap_draws=500,
        group_count=3,
    )
    second = run_transfer_ceiling_operating_characteristics(
        simulations_per_scenario=100,
        bootstrap_draws=500,
        group_count=3,
    )
    assert first.as_dict() == second.as_dict()
    assert first.generator_version == GENERATOR_VERSION
    assert len(first.scenarios) == 6
    assert {row.truth_ceiling for row in first.scenarios} == {"coarse", "fine"}
    for row in first.scenarios:
        assert row.exact_ceiling_recovery_rate + row.overreach_rate + row.underreach_rate == pytest.approx(1.0)
        assert 0.0 <= row.full_ceiling_rate <= 1.0


def test_contract_freezes_rules_before_first_full_run():
    contract = json.loads(
        (ROOT / "ODSP_TRANSFER_CEILING_OPERATING_CHARACTERISTICS_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["generator_version"] == GENERATOR_VERSION
    assert contract["fixed_design"]["simulations_per_scenario"] == 1000
    assert contract["frozen_before_first_1000_simulation_result"] is True
    assert contract["acceptance_rules"]["strong-full-normal-b20"] == "exact_ceiling_recovery_rate >= 0.90"
    assert contract["acceptance_rules"]["strong-full-normal-b50"] == "exact_ceiling_recovery_rate >= 0.98"
    assert "no acceptance threshold" in contract["acceptance_rules"]["weak-full-normal-b20"]
    boundary = contract["scientific_boundaries"]
    assert boundary["weak_positive_power_used_for_qualification"] is False
    assert boundary["historical_empirical_endpoint_rerun"] is False


def test_benchmark_rejects_invalid_design_arguments():
    with pytest.raises(ValueError, match="simulations_per_scenario"):
        run_transfer_ceiling_operating_characteristics(simulations_per_scenario=99)
    with pytest.raises(ValueError, match="bootstrap_draws"):
        run_transfer_ceiling_operating_characteristics(bootstrap_draws=499)
    with pytest.raises(ValueError, match="group_count"):
        run_transfer_ceiling_operating_characteristics(group_count=1)
    with pytest.raises(ValueError, match="step_correlation"):
        run_transfer_ceiling_operating_characteristics(step_correlation=1.0)
    with pytest.raises(ValueError, match="noise_standard_deviation"):
        run_transfer_ceiling_operating_characteristics(noise_standard_deviation=0.0)
