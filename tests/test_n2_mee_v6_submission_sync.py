from __future__ import annotations

import json
from pathlib import Path
import zipfile

from scripts.build_n2_mee_review_bundle_v6 import build_bundle
from scripts.build_n2_mee_submission_handoff_v6 import build_packet


ROOT = Path(__file__).resolve().parents[1]


def _members(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def test_v6_handoff_uses_population_amendment_without_reclassifying_primary():
    packet = build_packet()

    assert packet["generated_from_validated_v6_sources"] is True
    assert packet["abstract_word_count"] == 333
    assert len(packet["keywords"]) == 8
    assert packet["scientific_terminal_states"] == {
        "MH_ANTWERPEN": "empirical_state_prediction_unavailable",
        "BOP_RODENT": "empirical_state_prediction_mixed",
    }

    amendment = packet["bop_population_amendment"]
    assert amendment["post_outcome"] is True
    assert amendment["descriptive_only"] is True
    assert amendment["species_cluster_count"] == 4
    assert amendment["positive_individual_count"] == 27
    assert amendment["mean_total_gain_nats"] == 0.5709102207418053
    assert amendment["mean_total_gain_interval"][0] > 0
    assert amendment["new_individual_prediction_interval"][0] < 0
    assert amendment["empirical_p10"] > 0
    assert amendment["stepwise_population_ceiling"] == "pooled"
    assert amendment["can_reclassify_primary_endpoint"] is False

    assert packet["mechanical_submission_status"]["exact_upload_visual_approval_completed"] is False
    assert packet["submission_system_state"]["ready_for_submission"] is False
    assert all(value in (None, False) for value in packet["author_only_fields"].values())


def test_v6_review_bundle_contains_sanitized_population_evidence(tmp_path: Path):
    path = tmp_path / "review-v6.zip"
    build_bundle(path)
    files = _members(path)

    assert "manuscript/N2_MEE_MANUSCRIPT_DRAFT_v6.md" in files
    assert "odsp/population_transfer.py" in files
    assert "review_evidence/BOP_POPULATION_TRANSFER.json" in files
    assert "N2_MEE_STATE_PREDICTION_V6_CONTRACT.json" in files
    assert "BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_RECEIPT.json" not in files

    evidence = json.loads(
        files["review_evidence/BOP_POPULATION_TRANSFER.json"].decode("utf-8")
    )
    assert evidence["post_outcome_amendment"] is True
    assert evidence["internal_workflow_or_artifact_provenance_included"] is False
    assert evidence["primary_endpoint_preserved"]["terminal_category"] == "empirical_state_prediction_mixed"
    assert evidence["population_result"]["cluster_count"] == 4
    assert evidence["population_result"]["total_gain"]["mean_gain_lower"] > 0

    bundle_text = b"\n".join(files.values()).decode("utf-8", errors="ignore")
    assert "workflow_run_id" not in bundle_text
    assert "artifact_id" not in bundle_text


def test_v6_admin_surfaces_state_post_outcome_boundary_and_cluster_limit():
    cover = (
        ROOT / "manuscript" / "N2_MEE_COVER_LETTER_DRAFT_v6.md"
    ).read_text(encoding="utf-8")
    disclosures = (
        ROOT / "manuscript" / "N2_MEE_DISCLOSURE_DRAFTS_v6.md"
    ).read_text(encoding="utf-8")

    assert "post-outcome descriptive audits" in cover
    assert "species-cluster bootstrap interval" in cover
    assert "Only four species clusters are represented" in cover
    assert "not to reclassify the prospective endpoint" in cover

    assert "post-outcome BOP population-transfer summary" in disclosures
    assert "four represented species clusters" in disclosures
    assert "neither replaces the prospective pooled comparator" in disclosures
