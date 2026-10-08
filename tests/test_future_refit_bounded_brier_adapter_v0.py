from __future__ import annotations

import json
import numpy as np
import pytest

from odsp.future_refit_bounded_brier_adapter_v0 import (
    METHOD_VERSION,
    normalized_brier_filtration_gains,
)
from odsp.future_refit_shared_validation_evalue_v0 import (
    evaluate_future_refit_shared_validation_evalue_v0,
)

SHA = "b" * 64


def _fixture(R: int = 8, B: int = 48):
    N, K = 2 * B, 3
    y = (np.arange(N) % K).astype(int)
    wrong = (y + 1) % K
    predictions = np.empty((R, N, 3, K), dtype=float)
    predictions[:, :, 0, :] = np.eye(K)[wrong][None, :, :]
    predictions[:, :, 1, :] = 1.0 / K
    predictions[:, :, 2, :] = np.eye(K)[y][None, :, :]
    groups = tuple("g0" if i < B else "g1" for i in range(N))
    blocks = tuple(f"g{i//B}-block-{i % B:03d}" for i in range(N))
    ids = tuple(f"refit{i:03d}" for i in range(R))
    rows = tuple(f"row{i:03d}" for i in range(N))
    return predictions, y, ids, rows, groups, blocks


def _adapt(p, y, ids, rows):
    return normalized_brier_filtration_gains(
        p, y, refit_ids=ids, row_ids=rows
    )


def test_exact_simplex_produces_two_proper_bounded_positive_gains():
    p, y, ids, rows, *_ = _fixture()
    scored = _adapt(p, y, ids, rows)
    assert scored.method_version == METHOD_VERSION
    assert scored.score_tensor.shape == (8, 96, 3)
    assert scored.contrast_gains.shape == (8, 96, 2)
    assert np.allclose(scored.score_tensor[:, :, 0], 0.0)
    assert np.allclose(scored.score_tensor[:, :, 1], 2.0/3.0)
    assert np.allclose(scored.score_tensor[:, :, 2], 1.0)
    assert np.allclose(scored.contrast_gains[..., 0], 2.0/3.0)
    assert np.allclose(scored.contrast_gains[..., 1], 1.0/3.0)
    assert scored.contrast_gain_bounds == (-1.0, 1.0)
    assert scored.normalized_brier_score_bounds == (0.0, 1.0)
    assert scored.probability_simplex_verified is True
    assert scored.eligible_for_primary_route is False
    assert scored.training_process_iid_verified is False
    assert scored.independent_validation_blocks_verified is False
    assert json.loads(json.dumps(scored.metadata()))["contrast_count"] == 2


def test_bounded_gain_plugs_into_shared_sample_method_without_promotion():
    p, y, ids, rows, groups, blocks = _fixture()
    scored = _adapt(p, y, ids, rows)
    audit = evaluate_future_refit_shared_validation_evalue_v0(
        scored.contrast_gains,
        groups,
        blocks=blocks, refit_ids=ids,
        training_process_id="generated-scores-not-provenance",
        training_process_manifest_sha256=SHA,
        gain_lower_bound=-1.0,
        gain_upper_bound=1.0,
    )
    assert audit.certified_success_count == 8
    assert audit.group_count == 2
    assert audit.qualification_status == "experimental_unqualified"
    assert audit.model_to_score_provenance_verified is False
    assert audit.validation_iid_blocks_verified is False


def test_row_refit_permutation_is_equivariant():
    p, y, ids, rows, *_ = _fixture()
    a = _adapt(p, y, ids, rows)
    b = _adapt(
        p[::-1, ::-1], y[::-1], ids[::-1], rows[::-1]
    )
    assert np.allclose(a.contrast_gains[::-1, ::-1], b.contrast_gains)


@pytest.mark.parametrize("alter, match", [
    ("nan", "finite"),
    ("negative", r"\[0,1\]"),
    ("high", r"\[0,1\]"),
    ("not_sum1", "sum to one"),
    ("wrong_levels", "three_levels"),
    ("one_category", "categories"),
])
def test_malformed_probability_contract_fails_closed(alter, match):
    p, y, ids, rows, *_ = _fixture()
    if alter == "nan":
        p[0,0,0,0] = np.nan
    elif alter == "negative":
        p[0,0,1,0] = -0.1
    elif alter == "high":
        p[0,0,1,0] = 1.1
    elif alter == "not_sum1":
        p[0,0,1,:] = 0.0
    elif alter == "wrong_levels":
        p = p[:, :, :2, :]
    elif alter == "one_category":
        p = p[:, :, :, :1]
    with pytest.raises(ValueError, match=match):
        _adapt(p,y,ids,rows)


def test_missing_state_invalid_axis_and_duplicate_ids_fail_closed():
    p, y, ids, rows, *_ = _fixture()
    with pytest.raises(ValueError, match="integer"):
        _adapt(p, y.astype(float), ids, rows)
    with pytest.raises(ValueError, match="indices"):
        bad = y.copy()
        bad[0] = 3
        _adapt(p,bad,ids,rows)
    with pytest.raises(ValueError, match="unique"):
        _adapt(p,y,ids, ("row0",)*len(rows))
    with pytest.raises(ValueError, match="strictly nested"):
        normalized_brier_filtration_gains(
            p,y,refit_ids=ids,row_ids=rows,
            information_axes=((),("species",),("season",)),
        )


def test_theoretical_lower_and_upper_gain_endpoints_are_attainable():
    # Proper-score difference can equal -1 or +1 without clipping.
    p, y, ids, rows, *_ = _fixture()
    y0 = int(y[0])
    wrong = (y0 + 1) % 3
    p[0,0,0,:] = np.eye(3)[y0]
    p[0,0,1,:] = np.eye(3)[wrong]
    p[0,0,2,:] = np.eye(3)[y0]
    out = _adapt(p,y,ids,rows)
    assert out.contrast_gains[0,0,0] == pytest.approx(-1.0)
    assert out.contrast_gains[0,0,1] == pytest.approx(1.0)
