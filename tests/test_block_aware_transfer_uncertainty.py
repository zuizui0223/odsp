from __future__ import annotations

import numpy as np
import pytest

from odsp.block_aware_transfer_uncertainty import audit_block_aware_transfer_uncertainty


def test_block_bootstrap_can_downgrade_row_iid_pseudoreplication():
    block_means = np.asarray([-0.20, -0.10, 0.00, 0.05, 0.10, 0.15, 0.20, 0.25])
    gain = np.repeat(block_means, 100)
    groups = tuple(["g"] * gain.size)
    blocks = tuple(
        block_id
        for index in range(block_means.size)
        for block_id in [f"b{index}"] * 100
    )

    row_iid = audit_block_aware_transfer_uncertainty(
        gain,
        groups,
        bootstrap_draws=1000,
        seed=20260906,
        minimum_blocks_per_group=8,
    )
    clustered = audit_block_aware_transfer_uncertainty(
        gain,
        groups,
        blocks=blocks,
        bootstrap_draws=1000,
        seed=20260906,
        minimum_blocks_per_group=8,
    )

    assert row_iid.groups[0].lower_bound is not None
    assert row_iid.groups[0].lower_bound > 0.0
    assert row_iid.robust_transfer_category == "robust_generalizing"
    assert clustered.groups[0].lower_bound is not None
    assert clustered.groups[0].lower_bound <= 0.0
    assert clustered.robust_transfer_category == "uncertain"
    assert clustered.point_transfer_category == "generalizing"


def test_too_few_blocks_fails_closed():
    gain = np.repeat([0.2, 0.25, 0.3, 0.35], 20)
    groups = tuple(["g"] * gain.size)
    blocks = tuple(
        block_id for index in range(4) for block_id in [f"b{index}"] * 20
    )
    result = audit_block_aware_transfer_uncertainty(
        gain,
        groups,
        blocks=blocks,
        minimum_blocks_per_group=8,
        bootstrap_draws=500,
    )
    assert result.point_transfer_category == "generalizing"
    assert result.robust_transfer_category == "unavailable"
    assert result.robust_admissible is False
    assert result.unavailable_group_count == 1


def test_input_validation_rejects_invalid_bootstrap_settings():
    with pytest.raises(ValueError):
        audit_block_aware_transfer_uncertainty([0.1, 0.2], ["g", "g"], bootstrap_draws=10)
    with pytest.raises(ValueError):
        audit_block_aware_transfer_uncertainty([0.1, 0.2], ["g", "g"], confidence_level=1.0)
