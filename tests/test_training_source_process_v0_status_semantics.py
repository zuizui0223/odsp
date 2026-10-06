from __future__ import annotations

import json
from pathlib import Path


CONTRACT = Path("ODSP_TRAINING_SOURCE_PROCESS_V0_STATUS_SEMANTICS_CONTRACT.json")


def test_source_v0_status_semantics_separate_statistics_from_route_role():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    statistical = payload["statistical_status"]
    assert statistical["base_qualification_receipt_passed"] is True
    assert statistical["support_envelope_receipt_passed"] is True
    assert statistical["raw_numeric_method_status"] == "statistically_qualified"
    assert statistical["raw_numeric_surface_primary"] is False
    route = payload["route_status"]
    assert route["managed_wrapper_required_for_primary_route"] is True
    assert route["primary_route_registered_now"] is False


def test_source_v0_status_metadata_change_does_not_change_statistics():
    boundary = json.loads(CONTRACT.read_text(encoding="utf-8"))[
        "metadata_change_boundary"
    ]
    assert boundary["only_qualification_status_metadata_corrected"] is True
    assert boundary["numeric_estimator_changed"] is False
    assert boundary["variance_estimator_changed"] is False
    assert boundary["critical_value_changed"] is False
    assert boundary["calibration_recomputed"] is False
