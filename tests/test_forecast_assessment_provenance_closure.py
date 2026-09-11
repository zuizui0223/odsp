import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLOSURE = ROOT / "FORECAST_ASSESSMENT_PROVENANCE_CLOSURE.json"
V11_CONTRACT = ROOT / "FORECAST_ASSESSMENT_V11_CHECKPOINT_CONTRACT.json"
V11_RECEIPT = ROOT / "FORECAST_ASSESSMENT_V11_CHECKPOINT_VALIDATION_RECEIPT.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_closure_pins_v11_as_terminal_local_layer() -> None:
    closure = _load(CLOSURE)

    assert closure["closure_status"] == "closed_pending_external_trust_root_or_distinct_local_gap"
    assert closure["terminal_local_layer"] == "Forecast Assessment v11"
    assert closure["terminal_merge_commit"] == "7b258d2e050dccbf83dd742a41797192ae276a09"
    assert V11_CONTRACT.exists()
    assert V11_RECEIPT.exists()


def test_closure_preserves_provenance_statistical_separation() -> None:
    closure = _load(CLOSURE)
    local = closure["locally_closed_stack"]
    extension = closure["extension_rule"]

    assert local["provenance_failures_are_separate_from_statistical_uncertainty"] is True
    assert local["aggregate_confidence_score_emitted"] is False
    assert extension["any_future_extension_must_preserve_v11_frozen_contract_and_receipt"] is True
    assert extension["any_future_extension_must_preserve_provenance_statistical_separation"] is True
    assert extension["any_future_extension_must_not_reopen_closed_empirical_endpoints"] is True


def test_external_trust_claims_remain_false_and_match_v11_boundary() -> None:
    closure = _load(CLOSURE)
    v11 = _load(V11_CONTRACT)
    external = closure["external_trust_boundary"]
    claim = v11["claim_boundary"]

    assert external == {
        "external_timestamping_proven": False,
        "independent_witnessing_proven": False,
        "checkpoint_preexistence_proven": False,
        "real_world_access_history_completeness_proven": False,
        "whole_chain_and_checkpoint_cofabrication_prevented": False,
        "genuine_predeclaration_proven": False,
    }
    assert claim["clean_checkpoints_prove_external_timestamping"] is False
    assert claim["clean_checkpoints_prove_independent_witnessing"] is False
    assert claim["clean_checkpoints_prove_checkpoint_preexistence"] is False
    assert claim["clean_checkpoints_prevent_whole_chain_and_checkpoint_cofabrication"] is False
    assert claim["clean_checkpoints_prove_real_world_access_history_complete"] is False
    assert claim["clean_checkpoints_prove_genuine_predeclaration"] is False


def test_local_self_consistency_alone_cannot_justify_v12() -> None:
    closure = _load(CLOSURE)
    extension = closure["extension_rule"]

    assert extension["another_caller_supplied_local_hash_or_commitment_alone_justifies_v12"] is False
    assert extension["external_trust_claims_may_be_upgraded_by_local_self_consistency_alone"] is False
    assert extension["new_local_layer_requires_a_distinct_machine_checkable_gap_not_already_covered"] is True
    assert extension["new_external_trust_layer_requires_a_new_external_evidence_source_or_trust_root"] is True


def test_no_forecast_assessment_v12_surface_exists_while_closure_is_active() -> None:
    patterns = (
        "FORECAST_ASSESSMENT_V12*",
        "odsp/forecast_assessment_v12*",
        "docs/forecast_assessment_v12*",
        "scripts/run_forecast_assessment_v12*",
        "tests/test_forecast_assessment_v12*",
        ".github/workflows/forecast-assessment-v12*",
    )
    found = sorted(
        str(path.relative_to(ROOT))
        for pattern in patterns
        for path in ROOT.glob(pattern)
    )
    assert found == [], (
        "Forecast Assessment v12 surface appeared while local provenance closure is active: "
        + ", ".join(found)
    )


def test_closure_does_not_change_scientific_claims() -> None:
    closure = _load(CLOSURE)
    boundary = closure["scientific_boundary"]

    assert boundary["chapter_n2_empirical_chain_is_reopened"] is False
    assert boundary["gate_e_is_promoted"] is False
    assert boundary["forecast_assessment_closure_adds_a_statistical_estimand"] is False
    assert boundary["forecast_assessment_closure_adds_empirical_evidence"] is False
    assert boundary["forecast_assessment_closure_identifies_biological_mechanism"] is False
    assert boundary["forecast_assessment_closure_guarantees_future_performance"] is False
