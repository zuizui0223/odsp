from __future__ import annotations

from test_lane_policy import classify_test_path


def test_scientific_modules_default_to_core():
    examples = (
        "tests/test_niche_geometry.py",
        "tests/test_state_prediction.py",
        "tests/test_continuous_state_prediction.py",
        "tests/test_circular_state_prediction.py",
        "tests/test_joint_state_prediction.py",
        "tests/test_temporal_partition.py",
        "tests/test_transferability.py",
        "tests/test_bop_rodent_state_prediction.py",
        "tests/test_bop_species_baseline_amendment_receipt.py",
    )
    assert {classify_test_path(path) for path in examples} == {"core"}


def test_governance_stack_is_not_in_default_core_lane():
    examples = (
        "tests/test_forecast_assessment_v11.py",
        "tests/test_evaluation_access_log_chain_receipt.py",
        "tests/test_forecast_trust_dossier_v2.py",
        "tests/test_block_aware_transfer_uncertainty.py",
        "tests/test_model_refit_transfer_uncertainty.py",
        "tests/test_simultaneous_group_certification.py",
        "tests/test_training_provenance_audit.py",
    )
    assert {classify_test_path(path) for path in examples} == {"governance"}


def test_submission_artifacts_have_their_own_lane():
    examples = (
        "tests/test_n2_mee_review_package_v4.py",
        "tests/test_n2_mee_submission_handoff.py",
        "tests/test_n2_mee_anonymous_review_docx.py",
        "tests/test_n2_mee_state_prediction_v4_final_readiness_receipt.py",
    )
    assert {classify_test_path(path) for path in examples} == {"submission"}
