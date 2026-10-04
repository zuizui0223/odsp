from __future__ import annotations

import numpy as np
import pytest

from odsp.refit_information_transfer import RefitInformationLevelScores
from odsp.training_process_positive_transfer import (
    certify_training_process_positive_transfer_v1,
)
from odsp.training_process_positive_transfer_v2 import (
    certify_training_process_positive_information_transfer_v2,
    certify_training_process_positive_transfer_v2,
)


PROCESS_SHA = "b" * 64


def _rows(groups=2, blocks=8):
    g=[]; b=[]
    for gi in range(groups):
        for bi in range(blocks):
            g.append(f"g{gi}")
            b.append(f"g{gi}-b{bi}")
    return tuple(g), tuple(b)


def _audit(gain, **kwargs):
    groups, blocks = _rows()
    return certify_training_process_positive_transfer_v2(
        gain,
        groups,
        blocks=blocks,
        refit_ids=tuple(f"r{i:02d}" for i in range(np.asarray(gain).shape[0])),
        training_process_id="process-v2",
        training_process_manifest_sha256=PROCESS_SHA,
        bootstrap_draws=500,
        minimum_refits=8,
        minimum_blocks_per_group=8,
        **kwargs,
    )


def test_single_cell_iut_reduces_to_v1_max_t():
    groups=("g",)*8
    blocks=tuple(f"b{i}" for i in range(8))
    gain=np.repeat((0.35+np.linspace(-0.02,0.02,8))[None,:],8,axis=0)
    ids=tuple(f"r{i}" for i in range(8))
    v1=certify_training_process_positive_transfer_v1(
        gain,groups,blocks=blocks,refit_ids=ids,
        training_process_id="p",training_process_manifest_sha256=PROCESS_SHA,
        bootstrap_draws=500,minimum_refits=8,minimum_blocks_per_group=8,
    )
    v2=certify_training_process_positive_transfer_v2(
        gain,groups,blocks=blocks,refit_ids=ids,
        training_process_id="p",training_process_manifest_sha256=PROCESS_SHA,
        bootstrap_draws=500,minimum_refits=8,minimum_blocks_per_group=8,
    )
    c1=v1.contrasts[0].groups[0]
    c2=v2.contrasts[0].groups[0]
    assert c2.cellwise_critical_value == pytest.approx(v1.bootstrap_t_critical_value,abs=1e-12)
    assert c2.cellwise_lower_bound == pytest.approx(c1.lower_bound,abs=1e-12)


def test_global_and_claim_uses_iut_without_simultaneous_cellwise_ci_claim():
    groups,_=_rows()
    n=len(groups)
    gain=np.full((8,n,2),0.5)
    result=_audit(gain)
    assert result.global_category=="robust_generalizing"
    assert result.composition_rule=="intersection_union_all_component_cells_must_reject"
    assert result.additional_component_axis_multiplicity_correction_applied is False
    assert result.component_lower_bounds_are_simultaneous is False
    assert result.component_lower_bounds_support_global_conjunction_only is True


def test_one_failed_component_stops_global_claim():
    groups,_=_rows()
    n=len(groups)
    gain=np.full((8,n,2),0.5)
    gain[:,8:,1]=0.0
    result=_audit(gain)
    assert result.global_category=="not_robust_generalizing"
    assert result.contrasts[1].category=="not_robust_generalizing"


def test_other_cell_location_shifts_do_not_change_boundary_cell_test():
    groups,_=_rows()
    n=len(groups)
    rng=np.random.default_rng(99)
    gain=rng.normal(0,0.2,size=(8,n,2))
    base=_audit(gain,seed=777)
    moved=gain.copy()
    moved[:,:8,1]+=20.0
    moved[:,8:,0]+=30.0
    shifted=_audit(moved,seed=777)

    left=base.contrasts[0].groups[0]
    right=shifted.contrasts[0].groups[0]
    assert right.cellwise_critical_value == pytest.approx(left.cellwise_critical_value,abs=1e-12)
    assert right.cellwise_lower_bound == pytest.approx(left.cellwise_lower_bound,abs=1e-12)


def test_information_wrapper_keeps_non_skippable_iut_ceiling():
    groups,blocks=_rows()
    n=len(groups)
    pooled=np.zeros((8,n))
    coarse=np.full((8,n),0.4)
    fine=coarse+0.3
    result=certify_training_process_positive_information_transfer_v2(
        (
            RefitInformationLevelScores("pooled",(),pooled),
            RefitInformationLevelScores("coarse",("species",),coarse),
            RefitInformationLevelScores("fine",("species","context"),fine),
        ),
        groups,
        blocks=blocks,
        refit_ids=tuple(f"r{i}" for i in range(8)),
        training_process_id="process-v2",
        training_process_manifest_sha256=PROCESS_SHA,
        bootstrap_draws=500,
    )
    assert result.process_mean_certified_transfer_ceiling=="fine"
    assert result.component_intersection_union_used is True
    assert result.fixed_set_intersection_used is False
    assert result.historical_fixed_set_results_reclassified is False
