import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str) -> dict[str, object]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_manuscript_contract_matches_terminal_records():
    contract = _load("N2_MANUSCRIPT_CONTRACT.json")
    bat = _load("N2_BAT_THICKNESS_TERMINAL_DECISION.json")
    serengeti = _load("N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json")

    assert contract["primary_target"]["journal"] == "Methods in Ecology and Evolution"
    assert contract["primary_target"]["article_type"] == "Research Article"

    manuscript_bat = contract["terminal_empirical_values"]["bat"]
    assert manuscript_bat["terminal_category"] == bat["terminal_category"]
    assert manuscript_bat["information_nats_H_Z_given_XY"] == bat["primary"]["information_nats_H_Z_given_XY"]
    assert manuscript_bat["effective_vertical_states"] == bat["primary"]["effective_vertical_states"]
    assert manuscript_bat["heldout_gains"] == [
        score["mean_log_score_gain"] for score in bat["primary"]["sealed_individual_scores"]
    ]

    manuscript_serengeti = contract["terminal_empirical_values"]["serengeti"]
    assert manuscript_serengeti["terminal_category"] == serengeti["terminal_category"]
    assert manuscript_serengeti["admitted_species_count"] == serengeti["admitted_species_count"]
    assert manuscript_serengeti["information_nats_H_T_given_Site"] == serengeti["temporal_information_nats"]
    assert manuscript_serengeti["effective_temporal_states"] == serengeti["effective_temporal_states"]
    assert manuscript_serengeti["partition_information_nats_I_Species_T_given_Site"] == serengeti["partition_information_nats"]
    assert manuscript_serengeti["permutation_p_value"] == serengeti["permutation_p_value"]
    assert manuscript_serengeti["heldout_fold_gains"] == serengeti["heldout_gains"]


def test_manuscript_contract_preserves_n2_n3_boundary():
    contract = _load("N2_MANUSCRIPT_CONTRACT.json")
    serengeti = _load("N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json")

    assert serengeti["axis_resolved_state_allowed_for_empirical_n3"] is False
    assert any(
        "do not promote any terminal summary" in item
        for item in contract["claim_ceiling"]
    )


def test_explicit_license_file_matches_package_metadata():
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert license_text.startswith("MIT License")
    assert "Permission is hereby granted" in license_text
    assert 'license = {text = "MIT"}' in project


def test_numbered_abstract_has_four_sections_and_is_below_mee_limit():
    text = (ROOT / "docs" / "n2_numbered_abstract_draft_2026-09-04.md").read_text(encoding="utf-8")
    paragraphs = [line for line in text.splitlines() if line[:3] in {"1. ", "2. ", "3. ", "4. "}]
    assert len(paragraphs) == 4

    abstract_words = sum(len(paragraph.split()) - 1 for paragraph in paragraphs)
    assert abstract_words <= 350


def test_results_order_is_methods_first_not_dataset_first():
    contract = _load("N2_MANUSCRIPT_CONTRACT.json")
    order = contract["required_results_order"]

    assert order[0] == "known_truth_method_validation"
    assert order.index("bat_vertical_thickness") < order.index("bat_non_generalizing_organization")
    assert order.index("serengeti_temporal_thickness_and_partition") < order.index("serengeti_generalizing_transferability")
