from __future__ import annotations

import json
from pathlib import Path
import zipfile

from scripts.build_n2_mee_review_bundle_v6 import build_bundle
from scripts.build_n2_mee_submission_handoff_v6 import build_packet


ROOT = Path(__file__).resolve().parents[1]


def _validation(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "docx": "N2_MEE_ANONYMOUS_REVIEW_v6.docx",
                "checks": {"placeholder": True},
                "passed": True,
                "failed_checks": [],
                "nonempty_main_paragraph_count": 1,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_v6_submission_handoff_preserves_primary_and_exposes_population_summary(
    tmp_path: Path,
):
    packet = build_packet(_validation(tmp_path / "validation.json"))

    assert packet["generated_from_validated_v6_sources"] is True
    assert 330 <= packet["abstract_word_count"] <= 340
    assert len(packet["keywords"]) == 8
    assert packet["scientific_terminal_states"] == {
        "MH_ANTWERPEN": "empirical_state_prediction_unavailable",
        "BOP_RODENT": "empirical_state_prediction_mixed",
    }

    amendment = packet["bop_population_amendment"]
    assert amendment["post_outcome"] is True
    assert amendment["descriptive_secondary"] is True
    assert amendment["mean_total_gain_nats"] == 0.5709102207418053
    assert amendment["cluster_bootstrap_lower"] > 0
    assert amendment["positive_individuals"] == 27
    assert amendment["eligible_individuals"] == 30
    assert amendment["new_individual_prediction_lower"] < 0
    assert amendment["empirical_p10"] > 0
    assert amendment["represented_species_clusters"] == 4
    assert amendment["stepwise_population_ceiling"] == "pooled"
    assert amendment["can_reclassify_primary_endpoint"] is False

    assert packet["mechanical_submission_status"][
        "review_docx_v6_structurally_validated"
    ] is True
    assert packet["mechanical_submission_status"][
        "exact_upload_visual_approval_completed"
    ] is False
    assert all(value in (None, False) for value in packet["author_only_fields"].values())
    assert packet["submission_system_state"]["ready_for_submission"] is False


def test_v6_submission_admin_surfaces_name_post_outcome_population_boundary():
    cover = (
        ROOT / "manuscript" / "N2_MEE_COVER_LETTER_DRAFT_v6.md"
    ).read_text(encoding="utf-8")
    disclosures = (
        ROOT / "manuscript" / "N2_MEE_DISCLOSURE_DRAFTS_v6.md"
    ).read_text(encoding="utf-8")
    title = (
        ROOT / "manuscript" / "N2_MEE_TITLE_PAGE_TEMPLATE_v6.md"
    ).read_text(encoding="utf-8")

    assert "95% species-cluster bootstrap interval" in cover
    assert "does not reclassify the prospective mixed endpoint" in cover
    assert "post-outcome BOP population-transfer summary" in disclosures
    assert "only four represented species clusters" in disclosures
    assert "post-outcome BOP population-transfer summary" in title
    assert "[AUTHOR 1 FULL NAME]" in title


def test_v6_anonymous_bundle_contains_sanitized_population_evidence(tmp_path: Path):
    path = tmp_path / "review-v6.zip"
    first = build_bundle(path)
    first_bytes = path.read_bytes()

    second_path = tmp_path / "review-v6-second.zip"
    second = build_bundle(second_path)

    assert first_bytes == second_path.read_bytes()
    assert first["sha256"] == second["sha256"]

    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        assert "manuscript/N2_MEE_MANUSCRIPT_DRAFT_v6.md" in names
        assert "review_evidence/BOP_POPULATION_TRANSFER.json" in names
        assert "odsp/population_transfer.py" in names
        assert "tests/test_population_transfer.py" in names
        assert "BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_RECEIPT.json" not in names
        manifest = json.loads(archive.read("REVIEW_BUNDLE_MANIFEST.json"))
        evidence = json.loads(
            archive.read("review_evidence/BOP_POPULATION_TRANSFER.json")
        )

    assert manifest["schema_version"] == 6
    assert manifest["contains_author_identity"] is False
    assert manifest["contains_internal_workflow_or_pr_provenance"] is False
    assert manifest["contains_post_outcome_bop_population_transfer"] is True
    assert manifest["bop_primary_terminal_reclassified"] is False
    assert evidence["internal_workflow_or_artifact_provenance_included"] is False
    assert (
        evidence["primary_endpoint_preserved"]["terminal_category"]
        == "empirical_state_prediction_mixed"
    )
    assert evidence["population_result"]["total_gain"]["mean_gain_status"] == "positive"
