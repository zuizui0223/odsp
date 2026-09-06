from __future__ import annotations

import numpy as np
import pytest

from odsp.bias_robust_model_selection import evaluate_bias_robust_candidate
from odsp.forecast_trust_dossier_v3 import build_forecast_trust_dossier_v3
from odsp.joint_robustness_radius import audit_joint_robustness_radius


def _candidate_and_radius():
    gains=[];groups=[];blocks=[];covered=[]
    for gi in range(2):
        gid=f"g{gi+1}"
        for bi in range(8):
            bid=f"{gid}-b{bi+1}"
            for ri in range(10):
                gains.append(0.25+0.001*gi)
                groups.append(gid);blocks.append(bid)
                covered.append(ri<9)
    gain=np.asarray(gains,dtype=float)
    candidate=evaluate_bias_robust_candidate(
        "candidate",gain,np.zeros_like(gain),covered,groups,blocks,
        region_size=np.full(gain.size,4.0),gamma=1.0,
        confidence_level=0.95,bootstrap_draws=200,seed=20260906,
        minimum_blocks_per_group=8,
    )
    radius=audit_joint_robustness_radius(
        gain,groups,blocks,confidence_level=0.95,bootstrap_draws=200,
        seed=20260906,minimum_blocks_per_group=8,search_upper_gamma=4.0,
        binary_iterations=25,
    )
    return candidate,radius


def test_dossier_v3_adds_radius_without_confidence_score():
    candidate,radius=_candidate_and_radius()
    dossier=build_forecast_trust_dossier_v3(candidate,joint_radius_audit=radius)
    assert dossier.validation.validation_status=="admitted"
    assert dossier.joint_radius.status=="robust_through_search_upper"
    assert dossier.joint_radius.certified_gamma==4.0
    assert dossier.joint_radius.warnings==()
    assert dossier.decision_trace.operational_status=="admitted"
    assert dossier.aggregate_confidence_score_emitted is False


def test_dossier_v3_rejects_incompatible_radius_summary():
    candidate,radius=_candidate_and_radius()
    bad=radius.__class__(**{**radius.__dict__,"row_count":radius.row_count+1})
    with pytest.raises(ValueError):
        build_forecast_trust_dossier_v3(candidate,joint_radius_audit=bad)
