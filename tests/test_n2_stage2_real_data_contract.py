from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "N2_POOLED_REFERENCE_FAILURE_MODE_STAGE2_REAL_DATA_CONTRACT.json"


def _read() -> dict[str, object]:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_stage2_contract_requires_stage1_and_few_cluster_fix():
    contract = _read()
    prerequisites = contract["prerequisites"]

    assert contract["status"] == "pre_fresh_result_frozen"
    assert prerequisites["stage1_full_claim_supported"] is True
    assert prerequisites["few_cluster_fix_merge_sha"] == "6bc65a1a5575d61835838e711d6f0221af320034"
    assert prerequisites["bop_population_v2_receipt"] == "BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_RECEIPT_V2.json"


def test_stage2_has_exactly_two_failure_eligible_systems_and_one_semantic_control():
    contract = _read()
    systems = {row["system_id"]: row for row in contract["systems"]}

    assert set(systems) == {"BOP_RODENT", "PALMER_PENGUINS", "SNAPSHOT_SERENGETI"}
    assert contract["failure_eligible_system_count"] == 2
    assert contract["fresh_result_count"] == 1

    assert systems["BOP_RODENT"]["failure_mode_eligible"] is True
    assert systems["PALMER_PENGUINS"]["failure_mode_eligible"] is True
    assert systems["SNAPSHOT_SERENGETI"]["failure_mode_eligible"] is False
    assert systems["SNAPSHOT_SERENGETI"]["included_in_system_flip_denominator"] is False
    assert "species identity itself" in systems["SNAPSHOT_SERENGETI"]["semantic_reason_pooled_reference_is_appropriate"]


def test_penguins_fresh_proxy_analysis_is_frozen_before_result():
    contract = _read()
    penguins = next(
        row for row in contract["systems"] if row["system_id"] == "PALMER_PENGUINS"
    )

    assert penguins["fresh_outcome"] is True
    assert penguins["layer"] == "species"
    assert penguins["claimed_context"] == "four morphology measurements"
    assert penguins["validation"]["fold"] == "year"
    assert penguins["population_cluster"] == "collection year"

    learner = penguins["learner"]
    assert learner["kind"] == "random_forest"
    assert learner["random_state"] == 20260913
    assert learner["parameters"] == {
        "n_estimators": 300,
        "min_samples_leaf": 3,
        "n_jobs": 1,
    }
    assert learner["naive_model"] == "island ~ morphology"
    assert learner["audit_full_model"] == "island ~ species_onehot + morphology"
    assert learner["no_retuning_after_outcome"] is True

    accounting = penguins["score_accounting"]
    assert accounting["proxy_case_not_an_additive_identity_with_naive_model"] is True
    assert "context-only morphology model" in accounting["naive_pooled_gain"]
    assert "species+morphology model" in accounting["audit_context_gain"]


def test_bop_is_read_only_and_buteo_is_not_in_system_flip_denominator():
    contract = _read()
    bop = next(row for row in contract["systems"] if row["system_id"] == "BOP_RODENT")

    assert bop["fresh_outcome"] is False
    assert bop["model_refit"] is False
    assert bop["raw_data_reaccess"] is False
    assert bop["source"]["corrected_population_receipt"] == "BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_RECEIPT_V2.json"

    sentinel = bop["predeclared_motivating_sentinel"]
    assert sentinel["species"] == "Buteo buteo"
    assert sentinel["known_before_stage2_freeze"] is True
    assert sentinel["included_in_system_flip_denominator"] is False


def test_stage2_predeclares_reversal_downgrade_and_attenuation_separately():
    contract = _read()
    reporting = contract["primary_reporting"]

    assert reporting["system_flip_denominator"] == ["BOP_RODENT", "PALMER_PENGUINS"]
    assert reporting["prevalence_or_meta_analytic_rate_claimed"] is False
    assert set(reporting["report_counts_separately"]) == {
        "point_sign_reversal_count",
        "inferential_downgrade_count",
        "strong_attenuation_count",
    }

    decision = contract["fresh_penguins_decision"]
    assert decision["stage1_claim_reclassified_by_stage2"] is False
    assert "point_sign_reversal OR inferential_downgrade" in decision["fresh_empirical_reversal"]


def test_stage2_execution_is_one_shot_and_no_post_result_dataset_expansion():
    governance = _read()["governance"]

    assert governance["contract_must_merge_before_fresh_penguins_result_is_generated"] is True
    assert governance["penguins_stage2_execution_once"] is True
    assert governance["no_model_parameter_changes_after_result_access"] is True
    assert governance["no_layer_change_after_result_access"] is True
    assert governance["no_dataset_addition_to_primary_denominator_after_result_access"] is True
    assert governance["additional_public_reanalyses_after_stage2_are_stage4_or_exploratory"] is True
