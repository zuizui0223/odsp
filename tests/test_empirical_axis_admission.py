from odsp.empirical_axis_admission import (
    EmpiricalAxisArchitecture,
    assess_empirical_axis_architecture,
)


def _valid(**overrides):
    values = {
        "architecture_id": "native-xyz-example-v1",
        "axis_kind": "organism_vertical",
        "xy_and_axis_same_event": True,
        "axis_is_native_biological_or_structural_state": True,
        "effort_denominator_available": True,
        "prospective_abstention_if_effort_unavailable": False,
        "cluster_identifier_available": True,
        "source_precision_preserved": True,
        "sensor_schedule_or_effort_semantics_preserved": True,
        "public_reproducible_data": True,
        "source_version_pinnable": True,
        "structural_preflight_without_axis_outcomes": True,
        "contextual_proxy_used_as_axis": False,
        "upload_time_used_as_biological_time": False,
    }
    values.update(overrides)
    return EmpiricalAxisArchitecture(**values)


def test_valid_native_joint_event_architecture_is_admitted():
    result = assess_empirical_axis_architecture(_valid())
    assert result.admitted
    assert result.reasons == ()
    assert len(result.fingerprint) == 64


def test_sparse_secondary_linkage_is_rejected_before_axis_outcomes():
    result = assess_empirical_axis_architecture(
        _valid(xy_and_axis_same_event=False)
    )
    assert not result.admitted
    assert "xy_and_added_axis_not_joint_on_same_event" in result.reasons


def test_contextual_proxy_cannot_be_promoted_to_vertical_axis():
    result = assess_empirical_axis_architecture(
        _valid(
            axis_is_native_biological_or_structural_state=False,
            contextual_proxy_used_as_axis=True,
        )
    )
    assert not result.admitted
    assert "contextual_proxy_used_as_added_axis" in result.reasons


def test_upload_timestamp_cannot_be_biological_time():
    result = assess_empirical_axis_architecture(
        _valid(
            axis_kind="biological_time",
            upload_time_used_as_biological_time=True,
        )
    )
    assert not result.admitted
    assert "upload_time_used_as_biological_time" in result.reasons


def test_missing_effort_requires_predeclared_abstention_rule():
    rejected = assess_empirical_axis_architecture(
        _valid(
            effort_denominator_available=False,
            prospective_abstention_if_effort_unavailable=False,
        )
    )
    assert not rejected.admitted
    assert "effort_semantics_unavailable_without_abstention_rule" in rejected.reasons

    admitted = assess_empirical_axis_architecture(
        _valid(
            effort_denominator_available=False,
            prospective_abstention_if_effort_unavailable=True,
        )
    )
    assert admitted.admitted


def test_private_or_unpinnable_source_is_rejected():
    result = assess_empirical_axis_architecture(
        _valid(public_reproducible_data=False, source_version_pinnable=False)
    )
    assert not result.admitted
    assert "primary_data_not_publicly_reproducible" in result.reasons
    assert "source_not_version_pinnable" in result.reasons


def test_admission_is_deterministic_and_contains_no_outcome_fields():
    spec = _valid()
    first = assess_empirical_axis_architecture(spec)
    second = assess_empirical_axis_architecture(spec)
    assert first == second
    payload = first.as_dict()
    forbidden_fragments = ("entropy", "thickness", "projection", "log_score")
    assert not any(
        fragment in key.lower()
        for key in payload
        for fragment in forbidden_fragments
    )
