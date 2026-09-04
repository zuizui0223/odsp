from __future__ import annotations

import math

import numpy as np
import pytest

from odsp.niche_geometry import conditional_information, effective_conditional_states
from odsp.transferability import base_added_mutual_information, score_conditional_transferability


SEED = 20260904


def _positive(rng: np.random.Generator, shape: tuple[int, ...]) -> np.ndarray:
    return rng.gamma(1.4, 1.0, size=shape) + 0.02


def test_conditioning_monotonicity_and_chain_rule_across_random_supports():
    rng = np.random.default_rng(SEED)
    for _ in range(64):
        n_b, n_c, n_a = (int(v) for v in rng.integers(2, 7, size=3))
        support = _positive(rng, (n_b, n_c, n_a))

        h_a_given_b = conditional_information(support, base_axes=(0,), added_axes=(2,))
        h_a_given_bc = conditional_information(support, base_axes=(0, 1), added_axes=(2,))
        assert h_a_given_bc <= h_a_given_b + 2e-12

        h_c_given_b = conditional_information(support, base_axes=(0,), added_axes=(1,))
        h_ca_given_b = conditional_information(support, base_axes=(0,), added_axes=(1, 2))
        assert h_ca_given_b == pytest.approx(h_c_given_b + h_a_given_bc, abs=3e-12)

        eff_ca = effective_conditional_states(support, base_axes=(0,), added_axes=(1, 2))
        eff_c = effective_conditional_states(support, base_axes=(0,), added_axes=(1,))
        eff_a_given_bc = effective_conditional_states(support, base_axes=(0, 1), added_axes=(2,))
        assert eff_ca == pytest.approx(eff_c * eff_a_given_bc, abs=2e-10)


def test_adding_base_information_cannot_reduce_base_added_mutual_information():
    rng = np.random.default_rng(SEED + 1)
    for _ in range(64):
        shape = tuple(int(v) for v in rng.integers(2, 6, size=3))
        support = _positive(rng, shape)
        mi_a_b = base_added_mutual_information(support, base_axes=(0,), added_axes=(2,))
        mi_a_bc = base_added_mutual_information(support, base_axes=(0, 1), added_axes=(2,))
        assert mi_a_bc + 2e-12 >= mi_a_b


def test_deterministic_coarse_graining_obeys_data_processing_for_information():
    rng = np.random.default_rng(SEED + 2)
    for _ in range(64):
        n_b = int(rng.integers(2, 7))
        n_fine = int(rng.integers(4, 10))
        n_coarse = int(rng.integers(2, n_fine))
        fine = _positive(rng, (n_b, n_fine))

        mapping = np.empty(n_fine, dtype=int)
        mapping[:n_coarse] = np.arange(n_coarse)
        if n_fine > n_coarse:
            mapping[n_coarse:] = rng.integers(0, n_coarse, size=n_fine - n_coarse)
        rng.shuffle(mapping)

        coarse = np.zeros((n_b, n_coarse), dtype=float)
        for fine_state, coarse_state in enumerate(mapping):
            coarse[:, coarse_state] += fine[:, fine_state]

        h_fine = conditional_information(fine, base_axes=(0,), added_axes=(1,))
        h_coarse = conditional_information(coarse, base_axes=(0,), added_axes=(1,))
        mi_fine = base_added_mutual_information(fine, base_axes=(0,), added_axes=(1,))
        mi_coarse = base_added_mutual_information(coarse, base_axes=(0,), added_axes=(1,))

        assert h_coarse <= h_fine + 2e-12
        assert mi_coarse <= mi_fine + 2e-12
        assert effective_conditional_states(coarse, base_axes=(0,), added_axes=(1,)) <= (
            effective_conditional_states(fine, base_axes=(0,), added_axes=(1,)) + 2e-12
        )


def test_same_distribution_identity_holds_for_sparse_support_with_structural_zeros():
    rng = np.random.default_rng(SEED + 3)
    checked = 0
    for _ in range(128):
        n_b = int(rng.integers(2, 7))
        n_a = int(rng.integers(2, 8))
        support = _positive(rng, (n_b, n_a))
        keep = rng.random((n_b, n_a)) < 0.45

        # Ensure every base state has at least one supported added state so the
        # same-distribution held-out comparison is estimable.
        for base_state in range(n_b):
            if not np.any(keep[base_state]):
                keep[base_state, int(rng.integers(0, n_a))] = True
        support[~keep] = 0.0
        if not np.any(support > 0):
            continue

        mi = base_added_mutual_information(support, base_axes=(0,), added_axes=(1,))
        score = score_conditional_transferability(
            support,
            support,
            base_axes=(0,),
            added_axes=(1,),
        )
        assert score.mean_log_score_gain == pytest.approx(mi, abs=3e-12)
        checked += 1

    assert checked == 128


def test_unavailable_mask_makes_masked_numeric_contents_irrelevant():
    rng = np.random.default_rng(SEED + 4)
    for _ in range(32):
        shape = tuple(int(v) for v in rng.integers(2, 6, size=3))
        support = _positive(rng, shape)
        unavailable = rng.random(shape) < 0.25
        unavailable.flat[0] = False

        altered = support.copy()
        altered[unavailable] = 1e100

        h_original = conditional_information(
            support,
            base_axes=(0,),
            added_axes=(2,),
            unavailable_mask=unavailable,
        )
        h_altered = conditional_information(
            altered,
            base_axes=(0,),
            added_axes=(2,),
            unavailable_mask=unavailable,
        )
        mi_original = base_added_mutual_information(
            support,
            base_axes=(0,),
            added_axes=(2,),
            unavailable_mask=unavailable,
        )
        mi_altered = base_added_mutual_information(
            altered,
            base_axes=(0,),
            added_axes=(2,),
            unavailable_mask=unavailable,
        )
        assert h_altered == pytest.approx(h_original, abs=2e-12)
        assert mi_altered == pytest.approx(mi_original, abs=2e-12)


def test_effective_state_log_identity_is_exact_over_wide_cardinality_range():
    for added_cardinality in (2, 3, 5, 8, 13, 21):
        support = np.ones((4, added_cardinality), dtype=float)
        h = conditional_information(support, base_axes=(0,), added_axes=(1,))
        eff = effective_conditional_states(support, base_axes=(0,), added_axes=(1,))
        assert h == pytest.approx(math.log(float(added_cardinality)), abs=1e-12)
        assert eff == pytest.approx(float(added_cardinality), abs=1e-12)
