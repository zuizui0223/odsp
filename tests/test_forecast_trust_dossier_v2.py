from __future__ import annotations

import numpy as np

from odsp.bias_robust_model_selection import evaluate_bias_robust_candidate
from odsp.forecast_trust_dossier_v2 import build_forecast_trust_dossier_v2


def _small_candidate():
    gains=[];groups=[];blocks=[];covered=[]
    for gi in range(2):
        gid=f"g{gi+1}"
        for bi in range(8):
            bid=f"{gid}-b{bi+1}"
            for ri in range(4):
                gains.append(0.25+0.001*gi)
                groups.append(gid);blocks.append(bid)
                covered.append(ri!=0 or bi!=0)
    gains=np.asarray(gains,dtype=float)
    return evaluate_bias_robust_candidate(
        "candidate",
        gains,
        np.zeros_like(gains),
        covered,
        groups,
        blocks,
        region_size=np.full(gains.size,4.0),
        gamma=1.0,
        confidence_level=0.95,
        bootstrap_draws=200,
        seed=20260906,
        minimum_blocks_per_group=8,
    )


def test_dossier_v2_preserves_validation_when_optional_audits_absent():
    dossier=build_forecast_trust_dossier_v2(_small_candidate())
    assert dossier.validation.validation_status=="admitted"
    assert dossier.robustness_profile.sampling_weight_status=="not_audited"
    assert dossier.robustness_profile.bounded_reweighting_status=="not_audited"
    assert dossier.deployment.status=="not_audited"
    assert dossier.selection.status=="not_compared"
    assert dossier.decision_trace.operational_status=="admitted"
    assert dossier.decision_trace.blocking_reasons==()
    assert dossier.decision_trace.warning_reasons==()
    assert dossier.aggregate_confidence_score_emitted is False


def test_decision_trace_is_explicit_not_numeric_confidence():
    dossier=build_forecast_trust_dossier_v2(_small_candidate())
    assert dossier.decision_trace.trace[0]=="validation:admitted"
    assert dossier.decision_trace.trace[-1]=="selection:not_compared"
    assert "confidence" not in dossier.decision_trace.as_dict()
