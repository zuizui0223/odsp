from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from odsp.training_process_positive_iut import (
    _component_critical_values,
    certify_training_process_positive_iut_v2,
)


PROCESS_SHA = "b" * 64
ROOT = Path(__file__).resolve().parents[1]


def _rows(groups=2, blocks=8):
    g, b = [], []
    for gi in range(groups):
        for bi in range(blocks):
            g.append(f"g{gi}")
            b.append(f"g{gi}-b{bi}")
    return tuple(g), tuple(b)


def test_component_critical_values_are_columnwise_not_max_t():
    means = np.array([[0.1, 10.0], [0.2, 20.0], [-0.1, -10.0], [0.0, 0.0]])
    ses = np.ones_like(means)
    point = np.zeros(2)
    critical = _component_critical_values(
        means, ses, point, confidence_level=0.75
    )
    assert critical.shape == (2,)
    assert critical[1] > critical[0]


def test_iut_requires_every_component_but_does_not_claim_simultaneous_bounds():
    groups, blocks = _rows()
    n = len(groups)
    gain = np.full((8, n, 2), 0.5)
    result = certify_training_process_positive_iut_v2(
        gain,
        groups,
        blocks=blocks,
        refit_ids=tuple(f"r{i}" for i in range(8)),
        training_process_id="p",
        training_process_manifest_sha256=PROCESS_SHA,
        contrast_names=("a", "b"),
        bootstrap_draws=500,
    )
    assert result.compound_intersection_union_test is True
    assert result.all_required_components_must_reject is True
    assert result.additional_component_multiplicity_correction_applied is False
    assert result.component_test_independence_assumed is False
    assert result.component_lower_bounds_are_simultaneous is False
    assert result.arbitrary_any_cell_familywise_claim_allowed is False
    assert all(c.category == "robust_generalizing" for c in result.contrasts)


def test_single_failed_component_stops_compound_step():
    groups, blocks = _rows()
    n = len(groups)
    gain = np.full((8, n), 0.5)
    gain[:, :8] = 0.0
    result = certify_training_process_positive_iut_v2(
        gain,
        groups,
        blocks=blocks,
        refit_ids=tuple(f"r{i}" for i in range(8)),
        training_process_id="p",
        training_process_manifest_sha256=PROCESS_SHA,
        bootstrap_draws=500,
    )
    assert result.contrasts[0].category == "not_robust_generalizing"
    statuses = [cell.status for cell in result.contrasts[0].groups]
    assert "not_robust_positive" in statuses


def test_v2_contract_is_frozen_before_v2_calibration_results():
    method = json.loads(
        (ROOT / "ODSP_TRAINING_PROCESS_POSITIVE_IUT_V2_CONTRACT.json").read_text()
    )
    null = json.loads(
        (ROOT / "ODSP_TRAINING_PROCESS_POSITIVE_IUT_V2_NULL_CALIBRATION_CONTRACT.json").read_text()
    )
    power = json.loads(
        (ROOT / "ODSP_TRAINING_PROCESS_POSITIVE_IUT_V2_POWER_CALIBRATION_CONTRACT.json").read_text()
    )
    assert method["governance"]["v2_results_observed_before_contract_freeze"] is False
    assert method["governance"]["v2_primary_confirmatory"] is False
    assert null["prequalification_history"]["v2_null_results_observed_before_this_freeze"] is False
    assert power["prequalification_history"]["v2_power_results_observed_before_this_freeze"] is False
    assert power["prequalification_history"]["v1_power_threshold_retained_without_relaxation"] is True
    assert power["acceptance_rule"]["minimum_strong_terminal_power"] == 0.8
