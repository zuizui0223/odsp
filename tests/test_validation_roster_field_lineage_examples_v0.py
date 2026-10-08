"""Examples are literal source-method declarations, not real outcome data."""
from __future__ import annotations

import json
from pathlib import Path

from odsp.validation_roster_field_lineage_v0 import (
    audit_validation_roster_field_lineage_v0,
)

ROOT=Path(__file__).resolve().parents[1]


def test_snapshot_usa_photo_corrected_date_example_fails_to_admit_roster():
    raw=json.loads((
        ROOT/"examples/validation_roster_lineage/snapshot_usa_photo_corrected_hold.json"
    ).read_text())
    audit=audit_validation_roster_field_lineage_v0(raw)
    assert audit.selection_lineage_status=="HOLD_OUTCOME_DERIVED_SOURCE_METADATA"
    assert audit.affected_roles==("roster_membership",)
    assert audit.outcome_dependent_roles==("roster_membership",)
    assert any("first_photo_date" in path for path in audit.outcome_paths)
    assert any("last_photo_date" in path for path in audit.outcome_paths)
    assert any("<outcome-based correction>" in path for path in audit.outcome_paths)
    assert audit.trusted_external_lineage_attestation_verified is False
    assert audit.outcome_bytes_read is False


def test_hypothetical_original_site_allocation_still_not_qualified_primary():
    raw=json.loads((
        ROOT/"examples/validation_roster_lineage/hypothetical_predeclared_site_plan.json"
    ).read_text())
    audit=audit_validation_roster_field_lineage_v0(raw)
    assert audit.selection_lineage_status=="DECLARED_INDEPENDENT_LINEAGE_ONLY_NOT_ATTESTED"
    assert audit.outcome_dependent_roles==()
    assert audit.undocumented_roles==()
    assert audit.declared_source_lineage_independence_supported is True
    assert audit.trusted_external_lineage_attestation_verified is False
    assert audit.independently_observed_metadata_values_verified is False
    assert not audit.changes_active_odsp_qualified_routes
    assert not audit.retrospectively_reclassifies_old_ecological_results
