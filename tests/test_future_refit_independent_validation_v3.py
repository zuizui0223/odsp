from __future__ import annotations

import json
import math

import numpy as np
import pytest

from odsp.future_refit_independent_validation_v3 import (
    METHOD_VERSION,
    corrected_future_refit_lower_bound,
    evaluate_independent_validation_future_refit_v3,
    exact_iid_certificate_lower_bound,
)


PROCESS_SHA = "9" * 64


def _fixture(refits: int = 20):
    rng = np.random.default_rng(20261008)
    gains, groups, blocks = [], [], []
    for ri in range(refits):
        gains.append(0.5 + rng.normal(0.0, 0.02, size=(16, 2)))
        groups.append(tuple(f"g{gi}" for gi in range(2) for _ in range(8)))
        blocks.append(tuple(
            f"refit-{ri:03d}-g{gi}-block-{bi:02d}"
            for gi in range(2) for bi in range(8)
        ))
    ids = tuple(f"r{ri:03d}" for ri in range(refits))
    return gains, groups, blocks, ids


def _audit(data):
    gain, groups, blocks, ids = data
    return evaluate_independent_validation_future_refit_v3(
        gain, groups, blocks,
        refit_ids=ids,
        training_process_id="independent-validation-test",
        training_process_manifest_sha256=PROCESS_SHA,
    )


def test_exact_iid_binomial_and_false_certificate_correction_edges():
    assert exact_iid_certificate_lower_bound(0, 20) == 0.0
    assert exact_iid_certificate_lower_bound(20, 20) == pytest.approx(
        0.05 ** (1 / 20), abs=1e-14
    )
    assert corrected_future_refit_lower_bound(20, 20) == pytest.approx(
        (0.05 ** (1 / 20) - 0.05) / 0.95, abs=1e-14
    )
    assert corrected_future_refit_lower_bound(0, 20) == 0.0
    assert corrected_future_refit_lower_bound(8, 8) < 0.8
    assert [
        corrected_future_refit_lower_bound(k, 20)
        for k in range(21)
    ] == sorted(corrected_future_refit_lower_bound(k, 20) for k in range(21))


def test_all_certified_can_cross_exploratory_threshold_but_is_not_primary():
    out = _audit(_fixture())
    assert out.method_version == METHOD_VERSION
    assert out.certified_success_count == 20
    assert out.future_refit_success_probability_lower_bound > 0.8
    assert out.exceeds_exploratory_target is True
    assert out.validation_test_alpha_per_refit == 0.05
    assert out.process_confidence_alpha == 0.05
    assert out.confidence_alpha_is_sum_of_test_and_process_alphas is False
    assert out.globally_disjoint_validation_block_ids_checked is True
    assert out.independent_iid_validation_draws_verified is False
    assert out.frozen_process_iid_generation_verified is False
    assert out.holdout_independence_verified is False
    assert out.qualification_status == "experimental_unqualified"
    assert out.raw_api_primary_confirmatory is False
    assert all(not value for value in (
        out.fixed_set_results_reclassified,
        out.v5_process_mean_results_reclassified,
        out.v1_v2_results_reclassified,
    ))
    json.dumps(out.as_dict(), allow_nan=False)


def test_one_failed_group_contrast_vetoes_only_one_refit():
    gain, groups, blocks, ids = _fixture()
    gain[0][:8, 0] = np.linspace(-0.1, 0.1, 8)
    out = _audit((gain, groups, blocks, ids))
    assert out.certified_success_count == 19
    assert out.refits[0].certified_success is False
    assert all(refit.certified_success for refit in out.refits[1:])
    assert out.future_refit_success_probability_lower_bound < out.maximum_possible_future_refit_bound
    assert not out.exceeds_exploratory_target


def test_refit_order_invariance():
    fixture = _fixture()
    forward = _audit(fixture)
    gains, groups, blocks, ids = fixture
    backward = _audit((gains[::-1], groups[::-1], blocks[::-1], ids[::-1]))
    assert forward.as_dict() == backward.as_dict()


def test_validation_block_overlap_across_refits_fails_closed():
    gains, groups, blocks, ids = _fixture()
    blocks[1] = (blocks[0][0],) + blocks[1][1:]
    with pytest.raises(ValueError, match="overlap"):
        _audit((gains, groups, blocks, ids))


def test_zero_standard_error_and_minus_infinity_never_certify():
    gains, groups, blocks, ids = _fixture()
    gains[0][:8, 0] = 0.5
    gains[1][0, 1] = -math.inf
    out = _audit((gains, groups, blocks, ids))
    assert out.certified_success_count == 18
    assert any(c.status == "unavailable" for c in out.refits[0].cells)
    assert any(c.status == "unavailable" for c in out.refits[1].cells)
    json.dumps(out.as_dict(), allow_nan=False)


def test_malformed_group_or_insufficient_refits_fail_closed():
    gains, groups, blocks, ids = _fixture()
    groups[0] = ("g0",) * 16
    with pytest.raises(ValueError, match="two validation groups"):
        _audit((gains, groups, blocks, ids))
    with pytest.raises(ValueError, match="insufficient refits"):
        _audit(_fixture(7))


def test_binomial_overstatement_probability_under_worst_case_misclassification():
    # theta is at its largest possible value under given true p:
    # theta = p + (1-p)*a, with a=0.05.
    # Enumerating K gives an exact (not Monte Carlo) coverage check.
    n, a, process_alpha = 20, 0.05, 0.05
    for p in (0.0, 0.1, 0.5, 0.8, 0.95):
        theta = p + (1.0-p) * a
        risk = sum(
            math.comb(n,k) * theta**k * (1.0-theta)**(n-k)
            for k in range(n+1)
            if corrected_future_refit_lower_bound(
                k, n, test_alpha=a, process_alpha=process_alpha
            ) > p + 1e-12
        )
        assert risk <= process_alpha + 1e-12


def test_bad_input_rejected():
    with pytest.raises(ValueError, match="certificates cannot exceed"):
        corrected_future_refit_lower_bound(21, 20)
    with pytest.raises(ValueError, match="test_alpha"):
        corrected_future_refit_lower_bound(1, 20, test_alpha=0.5)
    gains, groups, blocks, ids = _fixture()
    gains[0][0,0] = np.nan
    with pytest.raises(ValueError, match="NaN"):
        _audit((gains, groups, blocks, ids))


def test_shared_validation_shock_can_break_the_binomial_coverage_bound():
    # Deliberate *invalid-design* negative control (NOT an accepted v3 case).
    # True refits are iid successes with p=0.8. A single common held-out-data
    # shock (probability a) incorrectly certifies all unsuccessful refits.
    # Each unsuccessful refit has marginal false-certification chance a, but
    # observed certificates are dependent, so K is NOT binomial.
    n, p, a = 20, 0.8, 0.05
    independent_truth_false_claim = sum(
        math.comb(n, k) * p**k * (1.0-p)**(n-k)
        for k in range(n+1)
        if corrected_future_refit_lower_bound(k, n) > p
    )
    shared_shock_false_claim = a + (1.0-a) * independent_truth_false_claim
    assert independent_truth_false_claim == pytest.approx(p**n)
    assert shared_shock_false_claim > 0.05
    # Shows why distinct block ID checks alone must never imply iid provenance.
