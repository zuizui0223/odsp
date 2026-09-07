import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_original_contract_bytes_and_prohibited_claims_are_unchanged():
    raw = (ROOT / 'MODEL_REFIT_TRANSFER_UNCERTAINTY_CONTRACT.json').read_bytes()
    git_blob = hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest()
    assert git_blob == '6edeb8e5be1b4fcdf2b479f24c26639217b6ee2c'
    contract = json.loads(raw)
    assert contract['contract_id'] == 'odsp-model-refit-transfer-uncertainty-v1'
    obligations = contract['known_truth_benchmark']['frozen_obligations']
    assert len(obligations) == 15
    for name, value in obligations.items():
        assert value is (name != 'aggregate_confidence_score_emitted')
    assert all(value is False for value in contract['claim_boundary'].values())
    assert all(value is False for value in contract['frozen_v4_boundary'].values())
    assert contract['definition']['same_selected_refit_is_shared_across_all_groups_within_a_nested_draw'] is True
    assert contract['decision_rule']['reference_fit_pass_does_not_rescue_refit_aware_uncertain'] is True
