from __future__ import annotations

import numpy as np

from odsp.robust_trust_aware_model_selection import (
    compare_robust_trust_candidates,
    evaluate_robust_trust_candidate,
)


def _candidate(name: str, block_means, *, region_size: float = 4.0, failed_coverage=False):
    gains=[]; groups=[]; blocks=[]
    for gi in range(2):
        gid=f"g{gi+1}"
        for bi,mean in enumerate(block_means):
            gains.extend([float(mean)]*25)
            groups.extend([gid]*25)
            blocks.extend([f"{gid}-b{bi+1}"]*25)
    gain=np.asarray(gains)
    marginal=np.full(gain.size,-2.0)
    covered=np.zeros(gain.size,dtype=bool)
    for gid in ("g1","g2"):
        idx=np.flatnonzero(np.asarray(groups,dtype=object)==gid)
        count=150 if (failed_coverage and gid=="g1") else int(round(0.90*idx.size))
        covered[idx[:count]]=True
    return evaluate_robust_trust_candidate(
        name,marginal+gain,marginal,covered,groups,blocks,
        region_size=np.full(gain.size,region_size),
        bootstrap_draws=1000,minimum_blocks_per_group=8,seed=20260906,
    )


def test_uncertainty_can_reject_point_trusted_candidate():
    weak=[-0.25,-0.20,-0.15,-0.10,-0.08,-0.06,-0.04,-0.02,0,0.02,0.04,0.06,0.08,0.10,0.12,0.14,0.16,0.18,0.20,0.22]
    candidate=_candidate("fragile",weak,region_size=3.0)
    assert candidate.point_and_coverage.trusted_admissible is True
    assert candidate.transfer_uncertainty.robust_transfer_category=="uncertain"
    assert candidate.robust_trusted_admissible is False


def test_pareto_uses_robust_only_candidates():
    strong=list(0.25+np.linspace(-0.03,0.03,20))
    broad=list(0.15+np.linspace(-0.02,0.02,20))
    a=_candidate("a",strong,region_size=4.0)
    b=_candidate("b",broad,region_size=7.0)
    result=compare_robust_trust_candidates([b,a],bootstrap_draws=1000,minimum_blocks_per_group=8)
    assert set(result.robust_trusted_names)=={"a","b"}
    assert result.pareto_front_names==("a",)
    assert result.recommended_by_log_score=="a"
    assert result.aggregate_confidence_score_emitted is False
