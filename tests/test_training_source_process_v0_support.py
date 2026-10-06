from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from odsp.training_source_process_v0_support import (
    GENERATOR_VERSION,
    SCENARIOS,
    _flatten,
    _support_world,
)


CONTRACT = Path("ODSP_TRAINING_SOURCE_PROCESS_V0_SUPPORT_CONTRACT.json")


def test_support_contract_matches_generator_identity_and_scenario_ids():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["run"]["seed"] == 20261018
    assert payload["run"]["simulations_per_scenario"] == 1000
    assert payload["acceptance_rule"]["maximum_accepted_component_rate"] == pytest.approx(
        0.06378404875209022
    )
    assert payload["selection_boundary"]["support_results_observed_before_freeze"] is False
    assert {row["scenario_id"] for row in payload["support_scenarios"]} == {
        row[0] for row in SCENARIOS
    }
    assert GENERATOR_VERSION == "nested_source_refit_support_v0"


def test_support_world_is_reproducible_finite_and_has_nested_shape():
    for stress in ("lognormal", "contaminated_inner", "rademacher", "normal", "heteroskedastic_inner"):
        a = _support_world(np.random.default_rng(12), stress, 8)
        b = _support_world(np.random.default_rng(12), stress, 8)
        assert a.shape == (8, 8, 6, 8, 2)
        assert np.array_equal(a, b)
        assert np.isfinite(a).all()


def test_unequal_validation_weights_repeat_by_group_without_changing_source_count():
    world = _support_world(np.random.default_rng(4), "normal", 8)
    declared = (0.5, 0.5, 1.0, 1.0, 2.0, 2.0, 4.0, 8.0)
    gain, groups, blocks, weights = _flatten(world, declared)
    assert gain.shape == (8, 8, 48, 2)
    assert len(groups) == len(blocks) == len(weights) == 48
    for group_index in range(6):
        start = group_index * 8
        np.testing.assert_allclose(weights[start:start+8], np.asarray(declared))


def test_heteroskedastic_inner_stress_changes_source_specific_inner_scale():
    normal = _support_world(np.random.default_rng(21), "normal", 8)
    hetero = _support_world(np.random.default_rng(21), "heteroskedastic_inner", 8)
    assert normal.shape == hetero.shape
    assert not np.array_equal(normal, hetero)
    assert np.isfinite(hetero).all()
