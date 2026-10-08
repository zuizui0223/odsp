"""V1 was irreversibly stopped on public-source semantics before valid inference.

Never rescue the old route by reinterpreting photo-corrected placement/retrieval
dates as a source-independent design. The original v1 contract and code remain
historical artifacts only.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FREEZE=ROOT/"ODSP_SNAPSHOT_USA_2024_CALENDAR_SPAN_V1_CONTRACT.json"
STOP=ROOT/"ODSP_SNAPSHOT_USA_2024_CALENDAR_V1_SOURCE_SEMANTICS_STOP.json"
YML=ROOT/".github/workflows/snapshot-usa-2024-calendar-span-v1.yml"


def test_stop_records_that_original_source_date_semantics_were_falsified():
    plan=json.loads(FREEZE.read_text())
    stop=json.loads(STOP.read_text())
    assert plan["status"]=="PRE_FIRST_CALENDAR_METADATA_RESULT_FROZEN_DESIGN"
    assert plan["primary_confirmatory_qualified"] is False
    assert stop["recorded_after_calendar_design_freeze"] is True
    assert stop["v1_status"]=="TERMINAL_HOLD_SOURCE_DATE_COLUMNS_ARE_IMAGE_DERIVED"
    assert stop["v1_source_selection_outcome_independent"] is False
    assert stop["v1_allowed_as_unopened_outcome_external_validation"] is False
    assert stop["v1_allowed_for_prospective_pre_outcome_sampling_design"] is False
    assert stop["v1_new_metadata_downloads_should_be_disabled"] is True
    assert stop["v1_code_original_retained_for_audit"] is True
    assert stop["v1_design_changed_or_posthoc_threshold_reoptimized"] is False
    assert stop["previously_queued_workflow_can_be_canceled_with_available_connector"] is False
    assert stop["queued_workflow_results_cannot_rescue_v1_eligibility"] is True
    assert stop["active_confirmatory_registry_modified"] is False
    assert stop["prior_public_empirical_results_reclassified"] is False


def test_current_workflow_does_not_schedule_new_deployment_downloads():
    text=YML.read_text()
    assert "Falsified source semantics" in text
    assert "snapshot_usa_2024_calendar_span_v1_first_receipt.json" in text
    assert "source_deployment_csv_download_attempted" in text
    assert "source_sequence_csv_opened" in text
    # Old numerical runner may remain in the repository for audit, but
    # current HEAD workflow must not call its download entrypoint.
    assert "--frozen-download" not in text
    assert "python scripts/screen_snapshot_usa_2024_calendar_span_v1.py" not in text
    assert "ODSP_SNAPSHOT_USA_2024_CALENDAR_V1_SOURCE_SEMANTICS_STOP.json" in text


def test_calendar_v1_stays_separate_from_v0_and_statistical_routes():
    stop=json.loads(STOP.read_text())
    frozen=json.loads(FREEZE.read_text())
    assert frozen["relationship"]["v0_selection_or_results_modified"] is False
    assert frozen["no_reclassification_of_prior_ecological_endpoints"] is True
    assert stop["v0_survey_nights_reclassified_as_unobserved_effort"] is False
    assert stop["v1_design_changed_or_posthoc_threshold_reoptimized"] is False
    assert stop["queued_workflow_results_cannot_rescue_v1_eligibility"] is True
