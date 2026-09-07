import json

import numpy as np
import pytest

from odsp.forecast_assessment import assess_state_forecast
from odsp.forecast_assessment_v2 import assess_state_forecast_v2


def _fixture():
    groups=[];blocks=[];gain=[]
    for gi in range(2):
        gid=f'g{gi}'
        for bi in range(10):
            for ri in range(4):
                groups.append(gid);blocks.append(f'{gid}-b{bi}')
                gain.append(.30+.002*gi+.001*bi+.0001*ri)
    gain=np.asarray(gain)
    covered=np.zeros(gain.size,dtype=bool)
    labels=np.asarray(groups,dtype=object)
    for gid in ('g0','g1'):
        idx=np.flatnonzero(labels==gid);covered[idx[:36]]=True
    return gain,tuple(groups),tuple(blocks),covered


def _kwargs():
    gain,groups,blocks,covered=_fixture()
    return dict(
        name='candidate',conditional_log_density=gain,marginal_log_density=np.zeros(gain.size),
        covered=covered,groups=groups,blocks=blocks,region_size=np.full(gain.size,4.0),
        validation_gamma=1.0,confidence_level=.95,bootstrap_draws=500,seed=20260907,
        minimum_blocks_per_group=4,
    )


def test_optional_extended_layers_preserve_v1_exactly():
    kwargs=_kwargs()
    v1=assess_state_forecast(**kwargs)
    v2=assess_state_forecast_v2(**kwargs)
    assert v2.base_assessment.as_dict()==v1.as_dict()
    assert v2.extended_certification.certification_status=='not_audited'
    assert v2.extended_certification.operational_status==v1.dossier.decision_trace.operational_status
    assert not v2.aggregate_confidence_score_emitted
    json.dumps(v2.as_dict(),allow_nan=False)


def test_simultaneous_and_identical_refits_can_certify():
    kwargs=_kwargs();gain=np.asarray(kwargs['conditional_log_density'])
    refits=np.repeat(gain[None,:],8,axis=0)
    result=assess_state_forecast_v2(
        **kwargs,run_simultaneous_group_certification=True,simultaneous_draws=500,
        refit_row_gain=refits,refit_nested_draws=500,minimum_refits=8,
    )
    assert result.extended_certification.certification_status=='certified'
    assert result.simultaneous_group_audit.max_t_transfer_category=='robust_generalizing'
    assert result.model_refit_audit.refit_aware_category=='robust_generalizing'
    assert result.refit_reference_match_error==0.0


def test_refit_reference_mismatch_is_rejected():
    kwargs=_kwargs();gain=np.asarray(kwargs['conditional_log_density'])
    refits=np.repeat(gain[None,:],8,axis=0);refits[0]+=1e-6
    with pytest.raises(ValueError,match='does not match'):
        assess_state_forecast_v2(**kwargs,refit_row_gain=refits,refit_nested_draws=500)


def test_block_definition_warning_does_not_rewrite_base_validation():
    kwargs=_kwargs();blocks=kwargs['blocks']
    coarse=tuple(f'{g}-pair-{i//8}' for i,g in enumerate(kwargs['groups']))
    result=assess_state_forecast_v2(
        **kwargs,alternative_block_definitions={'coarse':coarse},minimum_blocks_per_group=4,
    )
    assert result.base_assessment.dossier.validation.validation_status=='admitted'
    assert result.block_definition_audit is not None
    assert result.extended_certification.base_validation_status=='admitted'


def test_reserved_primary_block_name_and_empty_alternatives_rejected():
    kwargs=_kwargs()
    with pytest.raises(ValueError,match='at least one'):
        assess_state_forecast_v2(**kwargs,alternative_block_definitions={})
    with pytest.raises(ValueError,match='reserved'):
        assess_state_forecast_v2(**kwargs,alternative_block_definitions={'primary':kwargs['blocks']})
