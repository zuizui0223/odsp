from __future__ import annotations

import numpy as np
import pytest

from odsp.simultaneous_group_certification import audit_simultaneous_group_certification
from odsp.simultaneous_group_certification_v2 import (
    audit_simultaneous_group_certification_v2,
)


def _rows(block_count: int = 12):
    groups = ["a"] * block_count + ["b"] * block_count
    blocks = [f"a-{i:02d}" for i in range(block_count)] + [
        f"b-{i:02d}" for i in range(block_count)
    ]
    return groups, blocks


def test_v2_constant_gain_has_zero_studentizer_and_exact_positive_bounds():
    groups, blocks = _rows()
    result = audit_simultaneous_group_certification_v2(
        [0.25] * len(groups),
        groups,
        blocks=blocks,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
        seed=7,
    )

    assert result.schema_version == 2
    assert result.replicate_studentization_recomputed is True
    assert result.bootstrap_t_method == "replicate_studentized_cluster_ratio_bootstrap_t"
    assert result.bootstrap_t_critical_value == 0.0
    assert result.bootstrap_t_transfer_category == "robust_generalizing"
    for row in result.groups:
        assert row.studentizing_standard_error == pytest.approx(0.0)
        assert row.bootstrap_t_lower_bound == pytest.approx(0.25)
        assert row.bootstrap_t_upper_bound == pytest.approx(0.25)
        assert row.bootstrap_t_status == "robust_positive"


def test_v2_heterogeneous_blocks_use_distinct_bootstrap_and_studentizing_ses():
    groups, blocks = _rows()
    gain = []
    for group in ("a", "b"):
        for index in range(12):
            base = 0.2 if group == "a" else 0.3
            gain.append(base + 0.03 * ((index % 4) - 1.5))

    result = audit_simultaneous_group_certification_v2(
        gain,
        groups,
        blocks=blocks,
        bootstrap_draws=1000,
        minimum_blocks_per_group=8,
        seed=19,
    )

    assert result.bootstrap_t_critical_value is not None
    assert result.bootstrap_t_critical_value > 0
    assert result.bootstrap_t_transfer_category == "robust_generalizing"
    assert all(row.studentizing_standard_error is not None for row in result.groups)
    assert all(row.bootstrap_standard_error is not None for row in result.groups)
    assert any(
        abs(float(row.studentizing_standard_error) - float(row.bootstrap_standard_error))
        > 1e-8
        for row in result.groups
    )


def test_v2_is_invariant_to_row_order_and_common_weight_scale():
    groups, blocks = _rows()
    gain = np.asarray(
        [0.15 + 0.01 * (index % 6) for index in range(len(groups))],
        dtype=float,
    )
    weight = np.asarray(
        [1.0 + 0.2 * (index % 3) for index in range(len(groups))],
        dtype=float,
    )
    first = audit_simultaneous_group_certification_v2(
        gain,
        groups,
        blocks=blocks,
        sample_weight=weight,
        bootstrap_draws=1000,
        minimum_blocks_per_group=8,
        seed=101,
    )
    order = np.arange(len(groups))[::-1]
    second = audit_simultaneous_group_certification_v2(
        gain[order],
        [groups[index] for index in order],
        blocks=[blocks[index] for index in order],
        sample_weight=weight[order] * 1e6,
        bootstrap_draws=1000,
        minimum_blocks_per_group=8,
        seed=101,
    )

    assert second.bootstrap_t_critical_value == pytest.approx(
        first.bootstrap_t_critical_value,
        abs=1e-12,
    )
    assert second.bootstrap_t_transfer_category == first.bootstrap_t_transfer_category
    left = {row.group_id: row for row in first.groups}
    right = {row.group_id: row for row in second.groups}
    for group_id in left:
        assert right[group_id].mean_gain == pytest.approx(left[group_id].mean_gain, abs=1e-12)
        assert right[group_id].studentizing_standard_error == pytest.approx(
            left[group_id].studentizing_standard_error,
            abs=1e-12,
        )
        assert right[group_id].bootstrap_t_lower_bound == pytest.approx(
            left[group_id].bootstrap_t_lower_bound,
            abs=1e-12,
        )
        assert right[group_id].bootstrap_t_upper_bound == pytest.approx(
            left[group_id].bootstrap_t_upper_bound,
            abs=1e-12,
        )


def test_v2_fails_closed_when_too_few_positive_mass_blocks():
    groups, blocks = _rows(block_count=4)
    result = audit_simultaneous_group_certification_v2(
        [0.3] * len(groups),
        groups,
        blocks=blocks,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
    )
    assert result.bootstrap_t_critical_value is None
    assert result.bootstrap_t_transfer_category == "unavailable"
    assert result.unavailable_group_count == 2
    assert all(not row.estimable for row in result.groups)


def test_v1_remains_callable_for_frozen_receipt_provenance():
    groups, blocks = _rows()
    gain = [0.2 + 0.01 * (index % 4) for index in range(len(groups))]
    legacy = audit_simultaneous_group_certification(
        gain,
        groups,
        blocks=blocks,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
        seed=11,
    )
    prospective = audit_simultaneous_group_certification_v2(
        gain,
        groups,
        blocks=blocks,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
        seed=11,
    )
    assert legacy.max_t_critical_value is not None
    assert prospective.bootstrap_t_critical_value is not None
    assert prospective.schema_version == 2
