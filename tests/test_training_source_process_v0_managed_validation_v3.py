from __future__ import annotations
import json
from pathlib import Path

P=Path("ODSP_TRAINING_SOURCE_PROCESS_V0_MANAGED_INTERNAL_VALIDATION_CONTRACT_V3.json")

def test_source_v0_v3_corrects_deleted_duplicate_without_rewriting_v2():
    p=json.loads(P.read_text(encoding="utf-8"))
    c=p["correction"]
    assert c["v2_named_deleted_duplicate_scoring_module"] is True
    assert c["v2_rewritten"] is False
    assert c["canonical_scoring_surface"] == (
        "odsp.training_source_process_managed_scoring."
        "run_managed_training_source_process_scoring_v0"
    )
    assert c["canonical_bundle_loader"].endswith(
        "load_managed_training_source_score_bundle"
    )

def test_source_v0_v3_keeps_statistics_unchanged():
    p=json.loads(P.read_text(encoding="utf-8"))
    s=p["statistical_boundary"]
    assert s["numeric_source_v0_method_changed"] is False
    assert s["base_calibration_recomputed"] is False
    assert s["support_calibration_recomputed"] is False
    assert s["qualification_thresholds_changed"] is False
