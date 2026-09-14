from __future__ import annotations

import math

import numpy as np
import pytest

from odsp.bootstrap_t import (
    bootstrap_ratio_mean_and_cluster_se,
    ratio_mean_and_cluster_se,
    simultaneous_bootstrap_t_bounds,
    studentized_max_t_critical_value,
)


def test_ratio_cluster_se_matches_manual_unweighted_mean_formula():
    values = np.asarray([1.0, 2.0, 4.0, 5.0])
    numerator = values[:, None]
    weight = np.ones(values.size)

    mean, se = ratio_mean_and_cluster_se(numerator, weight)

    assert mean[0] == pytest.approx(np.mean(values))
    assert se[0] == pytest.approx(np.std(values, ddof=1) / math.sqrt(values.size))


def test_ratio_cluster_se_is_invariant_to_common_mass_rescaling():
    numerator = np.asarray([[2.0, 1.0], [6.0, 2.0], [3.0, 4.0], [9.0, 7.0]])
    weight = np.asarray([1.0, 2.0, 1.5, 3.0])
    mean, se = ratio_mean_and_cluster_se(numerator, weight)
    scaled_mean, scaled_se = ratio_mean_and_cluster_se(
        numerator * 1e7,
        weight * 1e7,
    )
    assert scaled_mean == pytest.approx(mean)
    assert scaled_se == pytest.approx(se)


def test_bootstrap_recomputes_studentizer_inside_each_draw():
    numerator = np.asarray([[0.0], [1.0], [4.0], [9.0]])
    weight = np.ones(4)
    sampled = np.asarray(
        [
            [0, 1, 2, 3],
            [0, 0, 1, 1],
            [2, 2, 3, 3],
            [0, 1, 1, 3],
        ],
        dtype=int,
    )

    means, ses = bootstrap_ratio_mean_and_cluster_se(numerator, weight, sampled)

    assert means.shape == (4, 1)
    assert ses.shape == (4, 1)
    assert ses[0, 0] == pytest.approx(
        np.std([0.0, 1.0, 4.0, 9.0], ddof=1) / math.sqrt(4)
    )
    assert len({round(float(value), 12) for value in ses[:, 0]}) > 1


def test_studentized_max_t_uses_replicate_specific_se():
    bootstrap_mean = np.asarray(
        [
            [1.2, 2.1],
            [0.8, 1.8],
            [1.1, 2.4],
            [0.9, 1.9],
        ]
    )
    bootstrap_se = np.asarray(
        [
            [0.2, 0.1],
            [0.1, 0.4],
            [0.5, 0.2],
            [0.2, 0.1],
        ]
    )
    point = np.asarray([1.0, 2.0])

    critical = studentized_max_t_critical_value(
        bootstrap_mean,
        bootstrap_se,
        point,
        confidence_level=0.75,
    )

    manual = []
    for mean_row, se_row in zip(bootstrap_mean, bootstrap_se):
        manual.append(max(abs(mean_row - point) / se_row))
    assert critical == pytest.approx(np.quantile(manual, 0.75))


def test_zero_dispersion_cell_is_zero_t_only_when_it_does_not_move():
    stable = studentized_max_t_critical_value(
        np.asarray([[1.0], [1.0], [1.0]]),
        np.asarray([[0.0], [0.0], [0.0]]),
        np.asarray([1.0]),
        confidence_level=0.95,
    )
    assert stable == 0.0

    moved = studentized_max_t_critical_value(
        np.asarray([[1.0], [1.1], [1.0]]),
        np.asarray([[0.0], [0.0], [0.0]]),
        np.asarray([1.0]),
        confidence_level=0.95,
    )
    assert math.isinf(moved)


def test_infinite_critical_value_fails_nonzero_se_cells_conservatively():
    lower, upper = simultaneous_bootstrap_t_bounds(
        np.asarray([0.2, 0.4]),
        np.asarray([0.0, 0.1]),
        math.inf,
    )
    assert lower[0] == upper[0] == pytest.approx(0.2)
    assert lower[1] == -math.inf
    assert upper[1] == math.inf
