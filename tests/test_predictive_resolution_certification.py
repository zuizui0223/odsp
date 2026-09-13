from __future__ import annotations

import math

from odsp.predictive_resolution_certification import certify_predictive_resolution


def _two_group_rows(n_per_group: int = 12):
    groups = ["a"] * n_per_group + ["b"] * n_per_group
    blocks = [f"a-{i}" for i in range(n_per_group)] + [
        f"b-{i}" for i in range(n_per_group)
    ]
    return groups, blocks


def test_joint_max_t_ceiling_stops_at_mixed_fine_resolution():
    groups, blocks = _two_group_rows()
    n = len(groups)
    pooled = [0.0] * n
    species = [0.4] * n
    context = [0.3] * 12 + [0.5] * 12

    result = certify_predictive_resolution(
        (
            ("pooled", pooled),
            ("species", species),
            ("context", context),
        ),
        groups,
        blocks=blocks,
        bootstrap_draws=800,
        minimum_blocks_per_group=8,
        seed=17,
    )

    assert result.point_transfer_ceiling == "species"
    assert result.certified_transfer_ceiling == "species"
    assert result.all_steps_estimable is True
    assert result.cell_count == 4
    assert result.estimable_cell_count == 4
    assert result.max_t_critical_value == 0.0
    assert result.steps[0].category == "robust_generalizing"
    assert result.steps[1].category == "mixed"
    assert [cell.status for cell in result.steps[0].groups] == [
        "robust_positive",
        "robust_positive",
    ]
    assert [cell.status for cell in result.steps[1].groups] == [
        "robust_nonpositive",
        "robust_positive",
    ]


def test_all_positive_steps_certify_final_resolution():
    groups, blocks = _two_group_rows()
    n = len(groups)
    result = certify_predictive_resolution(
        (
            ("pooled", [0.0] * n),
            ("species", [0.3] * n),
            ("context", [0.5] * n),
            ("full", [0.6] * n),
        ),
        groups,
        blocks=blocks,
        bootstrap_draws=600,
        minimum_blocks_per_group=8,
        seed=5,
    )

    assert result.point_transfer_ceiling == "full"
    assert result.certified_transfer_ceiling == "full"
    assert [step.category for step in result.steps] == [
        "robust_generalizing",
        "robust_generalizing",
        "robust_generalizing",
    ]


def test_insufficient_blocks_fail_closed_before_ceiling_advances():
    groups, _ = _two_group_rows()
    blocks = [f"a-{i}" for i in range(12)] + [f"b-{i % 4}" for i in range(12)]
    n = len(groups)
    result = certify_predictive_resolution(
        (
            ("pooled", [0.0] * n),
            ("species", [0.4] * n),
            ("full", [0.6] * n),
        ),
        groups,
        blocks=blocks,
        bootstrap_draws=600,
        minimum_blocks_per_group=8,
        seed=11,
    )

    assert result.all_steps_estimable is False
    assert result.estimable_cell_count == 2
    assert result.certified_transfer_ceiling == "pooled"
    assert all(step.category == "unavailable" for step in result.steps)
    assert all(step.unavailable_group_count == 1 for step in result.steps)


def test_nonfinite_final_failure_stops_certified_ceiling_but_keeps_earlier_step():
    groups, blocks = _two_group_rows()
    n = len(groups)
    full = [0.6] * n
    full[3] = -math.inf

    result = certify_predictive_resolution(
        (
            ("pooled", [0.0] * n),
            ("species", [0.4] * n),
            ("full", full),
        ),
        groups,
        blocks=blocks,
        bootstrap_draws=600,
        minimum_blocks_per_group=8,
        seed=23,
    )

    assert result.point_transfer_ceiling == "species"
    assert result.certified_transfer_ceiling == "species"
    assert result.steps[0].category == "robust_generalizing"
    assert result.steps[1].category == "unavailable"
    assert result.steps[1].unavailable_group_count == 1
    assert result.steps[1].groups[0].status == "unavailable"
    assert result.steps[1].groups[1].status == "robust_positive"


def test_block_bootstrap_is_deterministic_and_preserves_step_covariance():
    groups, blocks = _two_group_rows(14)
    n = len(groups)
    pooled = [0.0] * n
    species = []
    context = []
    for index, group in enumerate(groups):
        local = index % 14
        species_gain = 0.18 + 0.015 * ((local % 4) - 1.5)
        context_gain = 0.08 + 0.010 * ((local % 5) - 2.0)
        if group == "b":
            context_gain += 0.01
        species.append(species_gain)
        context.append(species_gain + context_gain)

    kwargs = dict(
        levels=(
            ("pooled", pooled),
            ("species", species),
            ("context", context),
        ),
        groups=groups,
        blocks=blocks,
        bootstrap_draws=900,
        minimum_blocks_per_group=8,
        seed=2026,
    )
    first = certify_predictive_resolution(**kwargs)
    second = certify_predictive_resolution(**kwargs)

    assert first.as_dict() == second.as_dict()
    assert first.max_t_critical_value is not None
    assert first.max_t_critical_value > 0.0
    assert first.certified_transfer_ceiling == "context"
    assert all(step.category == "robust_generalizing" for step in first.steps)


def test_rows_are_explicitly_marked_as_independence_assumption_without_blocks():
    groups, _ = _two_group_rows(10)
    n = len(groups)
    result = certify_predictive_resolution(
        (("pooled", [0.0] * n), ("full", [0.2] * n)),
        groups,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
        seed=2,
    )
    assert result.row_independence_assumed is True
    assert result.certified_transfer_ceiling == "full"
