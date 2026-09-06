import numpy as np
import pytest

from odsp.forecast_assessment import assess_state_forecast


def _simple_validation():
    groups=[];blocks=[];gain=[];covered=[];region=[]
    for gi in range(2):
        gid=f"g{gi+1}"
        for bi in range(4):
            bid=f"{gid}-b{bi+1}"
            for ri in range(5):
                groups.append(gid);blocks.append(bid);gain.append(0.20+0.01*gi)
                covered.append(not (bi==3 and ri>=1))
                region.append(3.0)
    return np.asarray(gain),np.asarray(covered,dtype=bool),tuple(groups),tuple(blocks),np.asarray(region)


def test_minimal_assessment_uses_same_rows_and_reports_optional_layers_not_audited():
    gain,covered,groups,blocks,region=_simple_validation()
    result=assess_state_forecast(
        "simple",gain,np.zeros_like(gain),covered,groups,blocks,
        region_size=region,target_coverage=0.80,coverage_tolerance=0.05,
        validation_gamma=1.0,bootstrap_draws=100,minimum_blocks_per_group=2,
    )
    assert result.row_count==gain.size
    assert result.candidate_name=="simple"
    assert result.dossier.validation.validation_status=="admitted"
    assert result.sampling_weight_audit is None
    assert result.bounded_reweighting_audit is None
    assert result.joint_radius.status=="not_audited"
    assert result.dossier.robustness_profile.sampling_weight_status=="not_audited"
    assert result.dossier.robustness_profile.bounded_reweighting_status=="not_audited"
    assert result.dossier.deployment.status=="not_audited"
    assert result.dossier.selection.status=="not_compared"
    assert result.aggregate_confidence_score_emitted is False


def test_assessment_composes_sampling_and_bounded_sensitivity_on_same_gain_rows():
    gain,covered,groups,blocks,region=_simple_validation()
    n=gain.size
    result=assess_state_forecast(
        "simple",gain,np.zeros_like(gain),covered,groups,blocks,
        region_size=region,target_coverage=0.80,coverage_tolerance=0.05,
        validation_gamma=1.0,bootstrap_draws=100,minimum_blocks_per_group=2,
        weight_scenarios={"uniform":np.ones(n),"scaled":np.full(n,2.0)},
        bounded_gamma=1.5,
    )
    assert result.sampling_weight_audit is not None
    assert result.sampling_weight_audit.sensitivity_category=="weight_robust_generalizing"
    assert result.bounded_reweighting_audit is not None
    assert result.bounded_reweighting_audit.envelope_transfer_category=="gamma_robust_generalizing"
    assert result.dossier.validation.validation_status=="admitted"


def test_assessment_rejects_partial_novelty_inputs_before_optional_model_fit():
    gain,covered,groups,blocks,region=_simple_validation()
    with pytest.raises(ValueError,match="supplied together"):
        assess_state_forecast(
            "simple",gain,np.zeros_like(gain),covered,groups,blocks,
            region_size=region,target_coverage=0.80,coverage_tolerance=0.05,
            validation_gamma=1.0,bootstrap_draws=100,minimum_blocks_per_group=2,
            novelty_train_X=np.ones((4,2)),
        )


def test_assessment_rejects_row_alignment_mismatch():
    gain,covered,groups,blocks,region=_simple_validation()
    with pytest.raises(ValueError,match="one value per validation row"):
        assess_state_forecast(
            "simple",gain,np.zeros_like(gain),covered[:-1],groups,blocks,
            region_size=region,target_coverage=0.80,coverage_tolerance=0.05,
            validation_gamma=1.0,bootstrap_draws=100,minimum_blocks_per_group=2,
        )
