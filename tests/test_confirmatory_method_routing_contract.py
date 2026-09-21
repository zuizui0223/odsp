from __future__ import annotations

import json
from pathlib import Path

from odsp.cli import main


CONTRACT = Path("ODSP_CONFIRMATORY_METHOD_ROUTING_CONTRACT.json")


def test_machine_contract_freezes_primary_and_nonprimary_roles():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["contract_id"] == "odsp-confirmatory-method-routing-v1"
    assert payload["roles"]["primary_confirmatory"]["positive_only"] is True
    assert payload["roles"]["bidirectional_confirmatory"]["primary_for_positive_only_claim"] is False
    assert payload["roles"]["sensitivity_only"]["can_be_primary"] is False
    assert payload["roles"]["unqualified"]["fail_closed"] is True
    assert payload["historical_governance"]["reclassify_frozen_empirical_endpoints"] is False


def test_machine_contract_freezes_calibrated_directional_family_sizes():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    scope = payload["directional_primary_scope"]
    assert scope["independent_filtration_contrast_counts"] == [2, 4]
    assert scope["paired_filtration_contrast_counts"] == [2]
    assert scope["paired_lattice_information_block_counts"] == [2, 3]
    assert scope["paired_lattice_edge_counts"] == [4, 12]
    assert scope["four_or_more_paired_lattice_blocks_primary"] is False


def test_machine_contract_freezes_calibrated_bidirectional_family_sizes():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    scope = payload["bidirectional_confirmatory_scope"]
    assert scope["independent_filtration_contrast_counts"] == [2, 4]
    assert scope["independent_lattice_information_block_counts"] == [2]
    assert scope["independent_lattice_edge_counts"] == [4]
    assert scope["twelve_edge_independent_lattice_qualified"] is False
    assert scope["paired_high_level_information_route_qualified"] is False
    assert scope["untouched_external_route_qualified"] is False


def test_machine_contract_marks_legacy_and_refit_mixture_as_sensitivity_only():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    surfaces = payload["surface_roles"]
    assert surfaces[
        "odsp.simultaneous_group_certification.audit_simultaneous_group_certification"
    ] == "sensitivity_only"
    assert surfaces[
        "odsp.refit_information_transfer.certify_refit_information_transfer"
    ] == "sensitivity_only"
    assert surfaces[
        "odsp.information_transfer_v2.certify_information_transfer_v2"
    ] == "bidirectional_confirmatory"
    assert surfaces[
        "odsp.information_transfer_positive_v2.certify_positive_information_transfer_v2"
    ] == "primary_confirmatory"


def test_machine_contract_requires_full_routing_context_for_primary_claim():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["surface_registry"]["surface_name_alone_establishes_primary_claim"] is False
    assert payload["surface_registry"]["full_routing_context_required_for_primary_claim"] is True


def test_method_route_cli_emits_machine_readable_decision(tmp_path: Path, capsys):
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps(
            {
                "alternative": "greater",
                "validation_design": "paired_shared_blocks",
                "information_structure": "complete_lattice",
                "upstream_refits": "fixed_set",
                "external_validation": "untouched_frozen",
                "information_block_count": 3,
            }
        ),
        encoding="utf-8",
    )
    code = main(["method-route", "--request", str(request), "--out", "-"])
    assert code == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["receipt_type"] == "odsp_confirmatory_method_route_v1"
    assert receipt["request"]["information_block_count"] == 3
    assert receipt["decision"]["role"] == "primary_confirmatory"
    assert receipt["decision"]["edge_count"] == 12
    assert receipt["decision"]["qualification_evidence"] == [
        "PAIRED_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json",
        "ODSP_ALL_REFIT_PAIRED_POSITIVE_LATTICE_CONTRACT.json",
        "ODSP_UNTOUCHED_EXTERNAL_PAIRED_ALL_REFIT_LATTICE_V4_CONTRACT.json",
    ]
    assert receipt["decision"]["cli_sequence"] == [
        "odsp freeze-refits-external-paired-lattice",
        "odsp transfer-refits-external-paired-lattice",
    ]
    assert receipt["governance"]["historical_endpoint_reclassification_allowed"] is False


def test_machine_contract_requires_registered_frozen_qualification_evidence():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    evidence = payload["qualification_evidence"]
    assert evidence["registry_file"] == "ODSP_CONFIRMATORY_CALIBRATION_EVIDENCE_REGISTRY.json"
    assert evidence["confirmatory_route_requires_registered_frozen_evidence"] is True
    assert evidence["family_scope_verified_against_frozen_receipts_in_ci"] is True
    assert evidence["runtime_recomputes_calibration"] is False
    assert evidence["unqualified_route_evidence_must_be_empty"] is True


def test_method_route_cli_fails_closed_on_invalid_request(tmp_path: Path, capsys):
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps(
            {
                "alternative": "greater",
                "validation_design": "paired_shared_blocks",
                "information_structure": "complete_lattice",
                "upstream_refits": "fixed_set",
                "external_validation": "untouched_frozen",
                "information_block_count": 4,
            }
        ),
        encoding="utf-8",
    )
    code = main(["method-route", "--request", str(request), "--out", "-"])
    assert code == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["decision"]["role"] == "unqualified"
    assert receipt["decision"]["primary_for_claim"] is False
    assert receipt["decision"]["edge_count"] == 32
