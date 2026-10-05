from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from odsp.training_process_cv3two_v5_support import (
    GENERATOR_VERSION,
    SCENARIOS,
    _primitive,
    _support_world,
    run_training_process_cv3two_v5_support_envelope,
)


CONTRACT = Path("ODSP_TRAINING_PROCESS_CV3TWO_V5_SUPPORT_ENVELOPE_CONTRACT.json")


def test_support_contract_matches_frozen_generator():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["qualification_run"]["seed"] == 20261015
    assert payload["qualification_run"]["simulations_per_scenario"] == 1000
    assert len(payload["support_scenarios"]) == len(SCENARIOS) == 5
    assert payload["base_qualification_boundary"]["support_scenario_outcomes_observed_before_this_freeze"] is False
    assert payload["acceptance_rule"]["maximum_accepted_component_rate"] == pytest.approx(
        0.06378404875209022
    )


def test_adversarial_primitives_are_reproducible_and_finite():
    for distribution in (
        "skewed_lognormal",
        "contaminated_normal",
        "rademacher",
        "heteroskedastic_interaction",
    ):
        a = _primitive(np.random.default_rng(11), (200,), distribution)
        b = _primitive(np.random.default_rng(11), (200,), distribution)
        assert np.array_equal(a, b)
        assert np.isfinite(a).all()


def test_support_world_has_expected_crossed_shape():
    world = _support_world(
        np.random.default_rng(1),
        distribution="heteroskedastic_interaction",
        refit_count=8,
        blocks_per_group=8,
        group_count=6,
        contrast_count=2,
        training_sd=0.2,
        validation_sd=0.2,
        interaction_sd=0.9,
    )
    assert world.shape == (8, 6, 8, 2)
    assert np.isfinite(world).all()


def test_support_runner_rejects_changed_family_size_before_simulation():
    with pytest.raises(ValueError, match="group_count"):
        run_training_process_cv3two_v5_support_envelope(group_count=5)
    with pytest.raises(ValueError, match="contrast_count"):
        run_training_process_cv3two_v5_support_envelope(contrast_count=4)
