import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_n2_to_n3_payload_schema_is_parseable_and_version_pinned():
    schema = json.loads((ROOT / "N2_TO_N3_PAYLOAD_SCHEMA.json").read_text())

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["schema_id"]["const"] == "n2-to-n3-payload-v1"
    assert schema["properties"]["program_id"]["const"] == "niche-to-survey-four-chapter-v1"
    assert schema["properties"]["producer"]["properties"]["chapter"]["const"] == "N2"
    assert (
        schema["properties"]["producer"]["properties"]["repository"]["const"]
        == "zuizui0223/odsp"
    )


def test_payload_schema_keeps_handoff_categories_distinct():
    schema = json.loads((ROOT / "N2_TO_N3_PAYLOAD_SCHEMA.json").read_text())
    categories = set(
        schema["$defs"]["handoff"]["properties"]["handoff_category"]["enum"]
    )

    assert categories == {
        "empirical_axis_resolved_supported",
        "known_truth_method_state_only",
        "descriptive_projection_only",
        "structural_capacity_only",
        "unavailable",
    }


def test_payload_schema_requires_integrity_fingerprints():
    schema = json.loads((ROOT / "N2_TO_N3_PAYLOAD_SCHEMA.json").read_text())

    assert "fingerprint" in schema["required"]
    assert schema["properties"]["fingerprint"]["pattern"] == "^[0-9a-f]{64}$"
    assert schema["$defs"]["state_artifact"]["properties"]["sha256"]["pattern"] == "^[0-9a-f]{64}$"
