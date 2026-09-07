import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_refit_scheme_sensitivity_contract_is_frozen_and_fail_closed():
    contract=json.loads((ROOT/"REFIT_SCHEME_SENSITIVITY_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["contract_id"]=="odsp-refit-scheme-sensitivity-v1"
    definition=contract["definition"]
    assert definition["same_untouched_validation_rows_required_across_schemes"] is True
    assert definition["each_scheme_uses_existing_model_refit_transfer_uncertainty_api"] is True
    assert definition["automatic_scheme_selection"] is False
    rule=contract["decision_rule"]
    assert rule["any_declared_scheme_unavailable_gives_category"]=="unavailable"
    assert rule["one_robust_scheme_cannot_override_another_scheme_failure"] is True
    obligations=contract["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations)==12
    for name,value in obligations.items():
        if name in {"no_automatic_scheme_selection","aggregate_confidence_score_emitted"}:
            assert value is False
        else:
            assert value is True
    assert all(value is False for value in contract["claim_boundary"].values())
    assert all(value is False for value in contract["frozen_v4_boundary"].values())
