from __future__ import annotations

import hashlib
import json

import pytest

from scripts.validate_bop_common_input_first_result_v1 import (
    CONTRACT,RECEIPT,validate_first_bop_transport_result,
)


def _first():
    receipt=json.loads(RECEIPT.read_text(encoding="utf-8"))
    contract=CONTRACT.read_bytes()
    return receipt,contract


def test_preregistered_contract_original_artifact_and_24_world_result_are_pinned():
    receipt,contract=_first()
    assert hashlib.sha256(contract).hexdigest()==receipt["frozen_contract"]["contract_sha256"]
    assert receipt["frozen_contract"]["contract_freeze_commit_sha"]==(
        "b32eed2503b94cbec0bab21daa4f20f765bb6fe0"
    )
    assert receipt["first_execution"]["workflow_run_id"]==40281982238
    assert receipt["first_execution"]["artifact_id"]==12633395633
    assert receipt["first_execution"]["original_result_json_byte_count"]==22614
    assert len(receipt["first_execution"]["original_result_world_audit_sha256"])==64
    assert receipt["first_result"]["covered_target_individuals"]==2599
    assert receipt["first_result"]["covered_validation_shift_individuals"]==757
    assert receipt["design"]["validation_independent_animals_per_condition"]==2880
    assert receipt["scientific_boundary"]["real_Dryad_candidate_admitted"] is False
    assert receipt["scientific_boundary"]["original_BOP_RF_direct_external_scoring_validated"] is False


def test_cannot_change_contract_or_first_artifact_provenance_without_error():
    receipt,contract=_first()
    with pytest.raises(ValueError,match="contract drifted"):
        validate_first_bop_transport_result({},receipt,contract+b" ")
    receipt["first_execution"]["artifact_id"]=1
    with pytest.raises(ValueError,match="provenance changed"):
        validate_first_bop_transport_result({},receipt,contract)


def test_fabricated_positive_claim_fails_before_world_scoring():
    receipt,contract=_first()
    test={
        "contract_id":"bop-common-input-transport-new-individual-v1",
        "contract_sha256":receipt["frozen_contract"]["contract_sha256"],
        "role":"prospective_known_truth_method_validation_only_not_real_BOP_or_Dryad_results",
        "original_BOP_terminal":"empirical_state_prediction_mixed",
        "original_RF_direct_external_transfer_admissible":True,
        "external_Dryad_candidate_admitted":True,
        "real_GPS_or_altitude_data_accessed":False,
        "passed":True,"checks":receipt["first_result"]["checks"],
        "worlds":24,"validation_individual_groups_each_condition":2880,
    }
    with pytest.raises(ValueError,match="claim ceiling"):
        validate_first_bop_transport_result(test,receipt,contract)
