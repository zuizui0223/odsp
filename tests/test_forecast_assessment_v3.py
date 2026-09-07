import numpy as np

from odsp.forecast_assessment_v3 import assess_state_forecast_v3


def _fixture():
    groups=[];blocks=[];gain=[]
    for g in range(2):
        gid=f"g{g}"
        for b in range(8):
            for r in range(4):
                groups.append(gid);blocks.append(f"{gid}-b{b}");gain.append(0.30+0.001*b)
    gain=np.asarray(gain)
    covered=np.zeros(gain.size,dtype=bool)
    ga=np.asarray(groups,dtype=object)
    for gid in ("g0","g1"):
        idx=np.flatnonzero(ga==gid);covered[idx[:29]]=True
    refits=np.repeat(gain[None,:],8,axis=0)
    schemes={"a":refits.copy(),"b":refits.copy()}
    ids={name:tuple(f"{name}-{i}" for i in range(8)) for name in schemes}
    refs={name:values[0] for name,values in ids.items()}
    return gain,covered,tuple(groups),tuple(blocks),schemes,ids,refs


def test_scheme_only_can_certify_without_rewriting_v2():
    gain,covered,groups,blocks,schemes,ids,refs=_fixture()
    result=assess_state_forecast_v3(
        "candidate",gain,np.zeros_like(gain),covered,groups,blocks,
        region_size=np.full(gain.size,4.0),validation_gamma=1.0,
        bootstrap_draws=500,minimum_blocks_per_group=8,
        refit_schemes=schemes,refit_ids_by_scheme=ids,
        reference_refit_ids_by_scheme=refs,scheme_nested_draws=500,
        scheme_minimum_refits=8,scheme_seed=20260907,
    )
    assert result.base_v2_assessment.extended_certification.certification_status=="not_audited"
    assert result.refit_scheme_audit is not None
    assert result.refit_scheme_audit.sensitivity_category=="scheme_robust_generalizing"
    assert result.v3_certification.certification_status=="certified"
    assert result.aggregate_confidence_score_emitted is False


def test_omitted_scheme_preserves_v2_certification_status():
    gain,covered,groups,blocks,_,_,_=_fixture()
    result=assess_state_forecast_v3(
        "candidate",gain,np.zeros_like(gain),covered,groups,blocks,
        region_size=np.full(gain.size,4.0),validation_gamma=1.0,
        bootstrap_draws=500,minimum_blocks_per_group=8,
    )
    assert result.refit_scheme_audit is None
    assert result.v3_certification.refit_scheme_status=="not_audited"
    assert result.v3_certification.certification_status==result.base_v2_assessment.extended_certification.certification_status
