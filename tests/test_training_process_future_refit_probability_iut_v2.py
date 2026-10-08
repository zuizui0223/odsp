from __future__ import annotations

import json

import numpy as np
import pytest

from odsp.training_process_future_refit_probability_iut_v2 import (
    METHOD_VERSION,
    certify_future_refit_probability_refit_iut_v2,
    certify_future_refit_probability_information_iut_v2,
)
from odsp.refit_information_transfer import RefitInformationLevelScores

SHA = "8" * 64

def _fixture(refits: int = 8):
    rng = np.random.default_rng(14)
    groups = tuple(f"g{g}" for g in range(2) for _ in range(8))
    blocks = tuple(f"g{g}-b{b}" for g in range(2) for b in range(8))
    gain = 1.2 + rng.normal(0.0, 0.03, size=(refits,len(groups),2))
    ids = tuple(f"r{i:02d}" for i in range(refits))
    return gain, groups, blocks, ids

def _evaluate(gain, groups, blocks, ids):
    return certify_future_refit_probability_refit_iut_v2(
        gain, groups,
        blocks=blocks, refit_ids=ids,
        training_process_id="prospective-v2",
        training_process_manifest_sha256=SHA,
    )

def test_refit_iut_success_uses_only_refit_axis_multiplicity():
    gain,groups,blocks,ids=_fixture()
    out=_evaluate(gain,groups,blocks,ids)
    assert out.method_version == METHOD_VERSION
    assert out.validation_component_alpha_per_refit == pytest.approx(0.025/8)
    assert out.refit_level_iut is True
    assert out.validation_multiplicity_across_refits_only is True
    assert out.max_t_across_all_refit_cells_used is False
    assert out.certified_success_count == 8
    assert out.future_refit_success_probability_lower_bound == pytest.approx(
        0.025 ** (1.0 / 8), abs=1e-12
    )
    assert out.raw_api_primary_confirmatory is False
    json.dumps(out.as_dict(), allow_nan=False)

def test_one_bad_group_contrast_vetoes_only_that_refit():
    gain,groups,blocks,ids=_fixture()
    gain[0,:8,0] = np.linspace(-0.01,0.01,8)
    out=_evaluate(gain,groups,blocks,ids)
    assert out.per_refit[0].certified_success is False
    assert all(row.certified_success for row in out.per_refit[1:])
    assert out.certified_success_count == 7
    assert out.future_refit_success_probability_lower_bound < out.maximum_possible_probability_bound

def test_refit_order_and_labels_are_invariant():
    gain,groups,blocks,ids=_fixture()
    one=_evaluate(gain,groups,blocks,ids)
    other=_evaluate(gain[::-1],groups,blocks,ids[::-1])
    assert one.as_dict()==other.as_dict()

def test_unavailable_nonfinite_gain_never_certifies_refit():
    gain,groups,blocks,ids=_fixture()
    gain[1,2,0]=-np.inf
    out=_evaluate(gain,groups,blocks,ids)
    assert out.per_refit[1].certified_success is False
    assert out.all_required_cells_estimable is False
    json.dumps(out.as_dict(), allow_nan=False)

def test_two_contrast_scope_and_alpha_budget_fail_closed():
    gain,groups,blocks,ids=_fixture()
    with pytest.raises(ValueError, match="exactly two"):
        _evaluate(gain[:,:,:1],groups,blocks,ids)
    with pytest.raises(ValueError, match="alpha budget"):
        certify_future_refit_probability_refit_iut_v2(
            gain,groups,blocks=blocks,refit_ids=ids,
            training_process_id="p",training_process_manifest_sha256=SHA,
            validation_alpha=0.04,process_alpha=0.025
        )

def test_information_wrapper_has_distinct_process_probability_target():
    gain,groups,blocks,ids=_fixture()
    pooled=np.zeros_like(gain[:,:,0])
    coarse=pooled+gain[:,:,0]
    fine=coarse+gain[:,:,1]
    info=certify_future_refit_probability_information_iut_v2(
        (
            RefitInformationLevelScores("pooled", (), pooled),
            RefitInformationLevelScores("coarse", ("species",), coarse),
            RefitInformationLevelScores("fine", ("species","context"), fine),
        ),groups,blocks=blocks,refit_ids=ids,
        training_process_id="p",
        training_process_manifest_sha256=SHA,
    )
    assert info.audit.certified_success_count == 8
    assert info.audit.process_mean_is_estimand is False
    assert info.audit.fixed_set_intersection_used is False
