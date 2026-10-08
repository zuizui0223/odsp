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
    assert scope["independent_fixed_set_untouched_external_lattice_primary"] is True
    assert scope["independent_fixed_set_untouched_external_lattice_information_block_counts"] == [2, 3]
    assert scope["independent_fixed_set_untouched_external_lattice_edge_counts"] == [4, 12]
    assert scope["predeclared_training_process_filtration_contrast_counts"] == [2]
    assert scope["predeclared_training_process_internal_primary"] is True
    assert scope[
        "predeclared_training_process_untouched_external_filtration_contrast_counts"
    ] == [2]
    assert scope["predeclared_training_source_process_filtration_contrast_counts"] == [2]
    assert scope["predeclared_training_source_process_internal_primary"] is True


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
    assert surfaces[
        "odsp.untouched_external_refit_independent_positive_lattice_contract_v5.run_untouched_external_independent_all_refit_lattice_contract_v5"
    ] == "primary_confirmatory"
    assert surfaces[
        "odsp.training_process_confirmatory_v5.certify_predeclared_training_process_positive_information_v5"
    ] == "primary_confirmatory"
    assert surfaces[
        "odsp.training_process_untouched_external_v5.run_untouched_external_training_process_v5"
    ] == "primary_confirmatory"
    assert surfaces[
        "odsp.training_source_process_managed_internal_v0.run_managed_internal_training_source_process_v0"
    ] == "primary_confirmatory"


def test_machine_contract_requires_full_routing_context_for_primary_claim():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["surface_registry"]["surface_name_alone_establishes_primary_claim"] is False
    assert payload["surface_registry"]["full_routing_context_required_for_primary_claim"] is True




def test_machine_contract_qualifies_process_mean_and_narrow_external_route():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    boundary = payload["refit_boundary"]
    assert boundary["predeclared_training_process_mean_claim_qualified"] is True
    assert boundary["predeclared_training_process_mean_is_conditional_on_frozen_training_source"] is True
    assert boundary["individual_future_refit_success_probability_claimed"] is False
    assert boundary["original_training_source_population_generalization_claimed"] is False
    external = payload["external_validation"]
    assert external["predeclared_training_process_untouched_external_primary"] is True
    assert external["predeclared_training_process_untouched_external_contrast_counts"] == [2]
    assert external["predeclared_training_process_declared_first_access_chronology_required"] is True
    assert external["predeclared_training_process_historical_nonaccess_machine_proven"] is False
    assert payload["qualification_evidence"]["registry"] == (
        "ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V7.json"
    )
    assert payload["qualification_evidence"]["content_lock_contract"] == (
        "ODSP_CONFIRMATORY_EVIDENCE_CONTENT_LOCK_V5.json"
    )
    assert boundary["predeclared_training_source_process_mean_claim_qualified"] is True
    assert boundary[
        "predeclared_training_source_process_mean_is_conditional_on_frozen_original_source_roster"
    ] is True
    assert boundary[
        "predeclared_training_source_process_unknown_ecological_superpopulation_generalization_claimed"
    ] is False


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
    assert receipt["decision"]["cli_sequence"] == [
        "odsp freeze-refits-external-paired-lattice",
        "odsp transfer-refits-external-paired-lattice",
    ]
    assert receipt["governance"]["historical_endpoint_reclassification_allowed"] is False


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
