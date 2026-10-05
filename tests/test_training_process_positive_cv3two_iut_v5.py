from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from odsp.refit_information_transfer import RefitInformationLevelScores
from odsp.training_process_positive_cv3two_iut import (
    _cv3two_components,
    certify_training_process_positive_cv3two_iut_v5,
    certify_training_process_positive_information_cv3two_iut_v5,
)


PROCESS_SHA = "5" * 64
CONTRACT = Path("ODSP_TRAINING_PROCESS_POSITIVE_CV3TWO_IUT_V5_CONTRACT.json")


def _rows(group_count: int = 2, block_count: int = 8):
    groups, blocks = [], []
    for g in range(group_count):
        for b in range(block_count):
            groups.append(f"g{g}")
            blocks.append(f"g{g}-b{b}")
    return tuple(groups), tuple(blocks)


def _audit(gain, **kwargs):
    groups, blocks = _rows()
    count = np.asarray(gain).shape[0]
    return certify_training_process_positive_cv3two_iut_v5(
        gain,
        groups,
        blocks=blocks,
        refit_ids=tuple(f"r{i:02d}" for i in range(count)),
        training_process_id="process-v5",
        training_process_manifest_sha256=PROCESS_SHA,
        minimum_refits=8,
        minimum_blocks_per_group=8,
        **kwargs,
    )


def test_v5_contract_was_frozen_before_results():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 5
    assert payload["qualification_plan"]["null_seed"] == 20261013
    assert payload["qualification_plan"]["power_seed"] == 20261014
    assert payload["qualification_plan"]["simulations_per_scenario"] == 1000
    assert payload["qualification_plan"]["maximum_accepted_component_rate"] == pytest.approx(
        0.06378404875209022
    )
    assert payload["qualification_plan"]["minimum_strong_terminal_power"] == 0.8
    assert payload["qualification_plan"]["v5_results_observed_before_this_freeze"] is False


def test_cv3two_is_exact_sum_of_row_and_block_jackknife_variances():
    rng = np.random.default_rng(9)
    numerator = rng.normal(size=(8, 11, 3))
    weight = rng.uniform(0.5, 2.0, size=11)
    point, vr, vb, vtwo = _cv3two_components(numerator, weight)
    np.testing.assert_allclose(vtwo, vr + vb, atol=1e-15)
    assert point.shape == (3,)


def test_translation_invariance_of_v5_bound():
    groups, _ = _rows()
    rng = np.random.default_rng(88)
    base = rng.normal(size=(8, len(groups), 2))
    first = _audit(base, contrast_names=("a", "b"))
    second = _audit(base + 0.73, contrast_names=("a", "b"))
    for lc, rc in zip(first.contrasts, second.contrasts):
        for left, right in zip(lc.groups, rc.groups):
            assert right.cv3two_standard_error == pytest.approx(
                left.cv3two_standard_error, abs=1e-12
            )
            assert right.lower_bound == pytest.approx(left.lower_bound + 0.73, abs=1e-12)


def test_v5_iut_semantics_and_t_df_are_explicit():
    groups, _ = _rows()
    result = _audit(np.full((8, len(groups), 2), 0.6))
    assert result.compound_intersection_union_test is True
    assert result.intersection_jackknife_subtraction_used is False
    assert result.additional_component_multiplicity_correction_applied is False
    assert result.component_lower_bounds_are_simultaneous is False
    assert result.t_degrees_of_freedom_rule == "min(refit_count, block_count)-1"
    for contrast in result.contrasts:
        for cell in contrast.groups:
            assert cell.t_degrees_of_freedom == 7
    json.dumps(result.as_dict(), allow_nan=False)


def test_refit_order_with_ids_is_invariant():
    groups, blocks = _rows()
    rng = np.random.default_rng(71)
    gain = rng.normal(loc=0.4, scale=0.2, size=(8, len(groups), 2))
    ids = tuple(f"r{i}" for i in range(8))
    kwargs = dict(
        groups=groups,
        blocks=blocks,
        training_process_id="p",
        training_process_manifest_sha256=PROCESS_SHA,
        contrast_names=("a", "b"),
    )
    first = certify_training_process_positive_cv3two_iut_v5(
        gain, refit_ids=ids, **kwargs
    )
    second = certify_training_process_positive_cv3two_iut_v5(
        gain[::-1], refit_ids=ids[::-1], **kwargs
    )
    assert first.as_dict() == second.as_dict()


def test_information_wrapper_keeps_non_skippable_ceiling():
    groups, blocks = _rows()
    n = len(groups)
    pooled = np.zeros((8, n))
    coarse = pooled + 0.5
    fine = coarse + 0.4
    result = certify_training_process_positive_information_cv3two_iut_v5(
        (
            RefitInformationLevelScores("pooled", (), pooled),
            RefitInformationLevelScores("coarse", ("species",), coarse),
            RefitInformationLevelScores("fine", ("species", "context"), fine),
        ),
        groups,
        blocks=blocks,
        refit_ids=tuple(f"r{i}" for i in range(8)),
        training_process_id="p",
        training_process_manifest_sha256=PROCESS_SHA,
    )
    assert result.process_mean_certified_transfer_ceiling == "fine"
    assert result.fixed_set_intersection_used is False
    assert result.historical_fixed_set_results_reclassified is False
