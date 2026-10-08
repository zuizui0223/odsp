from __future__ import annotations

import itertools
import json
import math

import numpy as np
import pytest

from odsp.future_refit_shared_validation_evalue_v0 import (
    METHOD_VERSION,
    _log_mixture_betting_e_value,
    certificate_probability_cp_lower,
    constant_block_gain_example,
    evaluate_future_refit_shared_validation_evalue_v0,
    shared_validation_design_frontier,
    shared_validation_success_probability_lower,
)

SHA = "7" * 64


def _fixture(refits: int = 20, blocks_per_group: int = 12):
    groups = tuple(f"g{gi}" for gi in range(2) for _ in range(blocks_per_group))
    blocks = tuple(f"g{gi}-b{bi}" for gi in range(2) for bi in range(blocks_per_group))
    gains = np.full((refits, len(groups), 2), 0.95, dtype=float)
    ids = tuple(f"r{ri:03d}" for ri in range(refits))
    return gains, groups, blocks, ids


def _run(fixture, **kwargs):
    gains, groups, blocks, ids = fixture
    return evaluate_future_refit_shared_validation_evalue_v0(
        gains, groups, blocks=blocks, refit_ids=ids,
        training_process_id="frozen-shared-validation-test",
        training_process_manifest_sha256=SHA,
        **kwargs,
    )


def test_positive_refits_certify_without_alpha_division_by_refit_count():
    result = _run(_fixture())
    assert result.method_version == METHOD_VERSION
    assert result.qualification_status == "experimental_unqualified"
    assert result.raw_api_primary_confirmatory is False
    assert result.certified_success_count == 20
    assert result.component_test_alpha == 0.002
    assert result.validation_markov_delta == 0.025
    assert result.process_alpha == 0.025
    assert result.maximum_bad_refit_false_certification_fraction == pytest.approx(.08)
    assert result.overall_confidence_alpha == pytest.approx(.05)
    assert result.conditional_certificate_cp_lower == pytest.approx(
        .025**(1/20), abs=1e-14
    )
    assert result.true_future_refit_success_probability_lower == pytest.approx(
        (.025**(1/20)-.08)/.92, abs=1e-14
    )
    assert result.true_future_refit_success_probability_lower > 0.8
    assert result.block_uniform_population_target is True
    assert result.shared_validation_blocks_used is True
    assert result.unconditional_certificate_count_binomial_claimed is False
    assert result.existing_results_reclassified is False
    assert not result.validation_iid_blocks_verified
    assert not result.training_process_iid_verified
    assert not result.bounded_score_protocol_verified
    json.dumps(result.as_dict(), allow_nan=False)


def test_one_boundary_cell_cancels_one_refit_only():
    gains, groups, blocks, ids = _fixture()
    gains[0, :12, 1] = 0.0
    out = _run((gains, groups, blocks, ids))
    assert out.certified_success_count == 19
    assert not out.refits[0].certified_success
    assert all(r.certified_success for r in out.refits[1:])
    assert out.true_future_refit_success_probability_lower < 0.8


def test_source_refit_permutation_does_not_change_result():
    fixture = _fixture()
    original = _run(fixture)
    g, groups, blocks, ids = fixture
    perm = _run((g[::-1], groups, blocks, ids[::-1]))
    assert original.as_dict() == perm.as_dict()


def test_shared_blocks_across_refits_are_permitted_and_not_treated_as_iid_certificates():
    out = _run(_fixture(refits=30))
    assert out.certified_success_count == 30
    assert out.component_test_alpha == 0.002
    assert out.unconditional_certificate_count_binomial_claimed is False


def test_zero_weight_rows_do_not_count_and_block_means_are_uniform():
    gains, groups, blocks, ids = _fixture()
    weights = [1.0]*len(groups)
    weights[:5] = [0.0] * 5
    # Five distinct group-0 blocks now lack support; only seven remain.
    with pytest.raises(ValueError, match="insufficient independent validation blocks"):
        _run((gains, groups, blocks, ids), sample_weight=weights)


def test_row_duplication_within_each_validation_block_is_invariant():
    gains, groups, blocks, ids = _fixture()
    original = _run((gains, groups, blocks, ids))
    doubled = _run((
        np.repeat(gains, 2, axis=1),
        tuple(x for g in groups for x in (g,g)),
        tuple(x for b in blocks for x in (b,b)),
        ids,
    ))
    assert original.true_future_refit_success_probability_lower == pytest.approx(
        doubled.true_future_refit_success_probability_lower
    )
    assert [r.certified_success for r in original.refits] == [
        r.certified_success for r in doubled.refits
    ]


def test_fail_closed_bounds_nan_insufficient_blocks_and_error_budget():
    gains, groups, blocks, ids = _fixture()
    gains[0, 0, 1] = 1.01
    with pytest.raises(ValueError, match="prospective bounds"):
        _run((gains, groups, blocks, ids))
    gains[0, 0, 1] = math.nan
    with pytest.raises(ValueError, match="NaN"):
        _run((gains, groups, blocks, ids))
    gains[0, 0, 1] = 0.95
    with pytest.raises(ValueError, match="invalid a, delta"):
        _run((gains, groups, blocks, ids), component_test_alpha=0.03)
    with pytest.raises(ValueError, match="invalid a, delta"):
        _run((gains, groups, blocks, ids), process_alpha=0.03)
    with pytest.raises(ValueError, match="gain_lower_bound"):
        _run((gains, groups, blocks, ids), gain_lower_bound=0.0)
    with pytest.raises(ValueError, match="insufficient independent validation blocks"):
        _run(_fixture(blocks_per_group=7))


def test_minus_infinity_as_unavailable_cannot_certify():
    gains, groups, blocks, ids = _fixture()
    gains[2, 1, 0] = -math.inf
    out = _run((gains, groups, blocks, ids))
    assert out.certified_success_count == 19
    assert any(c.status == "unavailable" for c in out.refits[2].cells)
    json.dumps(out.as_dict(), allow_nan=False)


def test_evalue_mixture_expectation_one_under_boundary_null():
    # Under iid X in {-1,+1} equally likely, E[X]=0.
    # Each fixed betting product has expectation 1, as does the mixture.
    B = 8
    values = [
        math.exp(_log_mixture_betting_e_value(
            np.array(bits, dtype=float), lower=-1.0, threshold=0.0))
        for bits in itertools.product((-1.0, 1.0), repeat=B)
    ]
    assert sum(values)/len(values) == pytest.approx(1.0, abs=1e-12)


def test_exact_shared_validation_common_shock_negative_control():
    # All refit certificates are dependent on a validation shock with prob 0.002.
    # In the no-shock case, S_r iid Bernoulli(p), all successes certify and
    # failures never certify. Under a shock every refit certifies, including
    # the truly unsuccessful ones. Corrected bound must control overclaim.
    R, p, a = 20, 0.8, 0.002
    risk_no_shock = sum(
        math.comb(R,k) * p**k * (1-p)**(R-k)
        for k in range(R+1)
        if shared_validation_success_probability_lower(k, R) > p
    )
    risk = a + (1-a) * risk_no_shock
    assert risk <= .05
    assert risk > 0


def test_cp_and_design_frontier_do_not_make_unconditional_binomial_power_claim():
    assert certificate_probability_cp_lower(0,20) == 0.0
    assert certificate_probability_cp_lower(20,20) == pytest.approx(.025**(1/20))
    f15 = shared_validation_design_frontier(15)
    assert f15["minimum_certificates"] is None
    f20 = shared_validation_design_frontier(20)
    assert f20["minimum_certificates"] == 20
    assert f20["minimum_distinct_shared_validation_blocks"] == 24
    assert f20["refit_by_block_score_evaluations"] == 480
    assert f20["unconditional_binomial_power_inferred"] is False
    assert f20["prospective_qualification_passed"] is False
    assert shared_validation_design_frontier(50)["minimum_certificates"] == 47



def test_constant_gain_feasibility_exposes_small_signal_block_demand():
    assert constant_block_gain_example(.95)["blocks_per_group"] == 11
    assert constant_block_gain_example(.2)["blocks_per_group"] == 41
    assert constant_block_gain_example(.05)["blocks_per_group"] == 153
    assert constant_block_gain_example(.05)["distinct_validation_blocks"] == 306
    assert constant_block_gain_example(.05)["prospective_power_qualified"] is False
    assert constant_block_gain_example(0.0)["certifiable"] is False
    assert constant_block_gain_example(.02, maximum_blocks_per_group=100)["certifiable"] is False
    with pytest.raises(ValueError, match="frozen score bounds"):
        constant_block_gain_example(1.01)
