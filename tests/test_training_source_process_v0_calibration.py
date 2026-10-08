from __future__ import annotations

import math
import numpy as np
import pytest

from odsp.training_source_process_v0_calibration import (
    GENERATOR_VERSION,
    SCENARIOS,
    _oracle_se,
    _world,
)


def test_source_v0_generator_identity_and_scenarios_are_frozen():
    assert GENERATOR_VERSION == "nested_source_refit_x_validation_c2_v0"
    assert len(SCENARIOS) == 6
    ids=[row[0] for row in SCENARIOS]
    assert "inner-dominant-normal-s20-r8-b20" in ids
    assert "balanced-t3-s8-r8-b20" in ids


def test_source_v0_world_has_nested_source_refit_crossed_validation_shape():
    world=_world(
        np.random.default_rng(1),
        distribution="normal",
        source_count=8,
        inner_count=8,
        blocks=8,
        groups=6,
        contrasts=2,
        source_sd=0.5,
        inner_sd=0.5,
        validation_sd=0.5,
        source_validation_sd=0.5,
        inner_validation_sd=0.5,
    )
    assert world.shape == (8,8,6,8,2)
    assert np.isfinite(world).all()


def test_oracle_se_matches_frozen_variance_decomposition():
    observed=_oracle_se(8,8,8,0.5,0.5,0.5,0.5,0.5)
    expected=math.sqrt(
        0.5**2/8
        + 0.5**2/(8*8)
        + 0.5**2/8
        + 0.5**2/(8*8)
        + 0.5**2/(8*8*8)
    )
    assert observed == pytest.approx(expected, abs=1e-15)


def test_student_t3_primitive_is_variance_standardized_in_large_draw():
    from odsp.training_source_process_v0_calibration import _primitive
    x=_primitive(np.random.default_rng(7),(200000,),"student_t3")
    assert abs(float(np.mean(x))) < 0.02
    assert abs(float(np.var(x))-1.0) < 0.08
