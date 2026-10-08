"""Synthetic-only camera-operation package guard with animal-event embargo."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import zipfile

import pytest

from odsp.uljin_operation_log_header_preflight_v0 import (
    OPERATION, EVENTS, MANIFEST,
    inspect_uljin_operation_header_only,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads(
    (ROOT/"ULJIN_OPERATION_METADATA_HEADER_PREFLIGHT_V0_CONTRACT.json").read_text()
)

PRIVATE_DETECTION_VALUE="UNREAD_ENDANGERED_UNGULATE_DETECTED_AT_03_14_09"


def _zip(ops=None, *, omit=None, extra=()):
    if ops is None:
        ops=(
            "Station,DeploymentStart,DeploymentEnd,DowntimeStart,DowntimeEnd\n"
            "UJ1_SECRETS,2022-05-01T00:00,2022-08-14T23:59,,\n"
        )
    elements={
        OPERATION:ops,
        EVENTS:"Station,Species,Date,Time\n"+
            f"UJ1_PRIVATE,{PRIVATE_DETECTION_VALUE},2022-05-01,03:14:09\n",
        MANIFEST:"source_version\tsha256\nsource_file_v1.1\tunverified\n",
    }
    if omit:
        elements.pop(omit)
    for name,content in extra:
        elements[name]=content
    buff=io.BytesIO()
    with zipfile.ZipFile(buff,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in elements.items():
            z.writestr(name,data)
    return buff.getvalue()


def test_first_operation_line_only_reproduces_non_admission_receipt(monkeypatch):
    data=_zip()
    original_open=zipfile.ZipFile.open
    opened=[]
    def spy(self,name,*args,**kwargs):
        key=name.filename if isinstance(name,zipfile.ZipInfo) else name
        opened.append(key)
        if key!=OPERATION:
            raise AssertionError("preflight tried to open a non-operation member")
        return original_open(self,name,*args,**kwargs)
    monkeypatch.setattr(zipfile.ZipFile,"open",spy)
    out=inspect_uljin_operation_header_only(data,PLAN)
    assert opened==[OPERATION]
    assert out["source_archive_sha256"]==hashlib.sha256(data).hexdigest()
    assert out["expected_operation_path_found"]
    assert out["expected_detection_path_name_found_but_not_opened"]
    assert out["operation_header_field_count"]==5
    assert out["animal_detection_member_opened"] is False
    assert out["operation_data_rows_read"] is False
    assert out["hourly_camera_uptime_or_detection_effort_verified"] is False
    assert out["source_archive_version_attested"] is False
    assert out["primary_ecological_result_qualified"] is False
    report=json.dumps(out,allow_nan=False)
    assert PRIVATE_DETECTION_VALUE not in report
    assert "UJ1_SECRETS" not in report
    assert "UJ1_PRIVATE" not in report


@pytest.mark.parametrize("missing", [OPERATION,EVENTS,MANIFEST])
def test_expected_source_package_names_missing_stop_before_any_result(missing):
    with pytest.raises(ValueError,match="missing"):
        inspect_uljin_operation_header_only(_zip(omit=missing),PLAN)


def test_duplicate_header_fields_and_malformed_quotes_fail_closed():
    with pytest.raises(ValueError,match="duplicate operation"):
        inspect_uljin_operation_header_only(
            _zip(ops="Station,Station,Start,End\nidentity,secret,2022,2023\n"),PLAN
        )
    with pytest.raises(ValueError,match="unterminated"):
        inspect_uljin_operation_header_only(
            _zip(ops='Station,"unterminated\nid,secret\n'),PLAN
        )


def test_unsafe_path_rejected_before_any_member_read():
    for path in ("../outside.txt","/absolute.txt"):
        with pytest.raises(ValueError,match="unsafe path"):
            inspect_uljin_operation_header_only(
                _zip(extra=((path,"should never be accessed"),)),PLAN
            )


def test_unknown_archive_schema_does_not_prove_uptime():
    out=inspect_uljin_operation_header_only(
        _zip(ops="Mystery,NoTimestampAtAll\nredacted,redacted\n"),PLAN
    )
    assert out["operation_header_names"]==["Mystery","NoTimestampAtAll"]
    assert out["hourly_camera_uptime_or_detection_effort_verified"] is False
    assert out["camera_operation_metadata_originally_observation_independent_verified"] is False
    assert out["status"]=="STRUCTURAL_OPERATION_HEADER_ONLY_NOT_ELIGIBLE_FOR_OUTCOME_ACCESS"


def test_contract_change_and_unparseable_source_fail_closed():
    contract=json.loads(json.dumps(PLAN))
    contract["preflight"]["forbid_opening_any_detection_file"]=False
    with pytest.raises(ValueError,match="security limits"):
        inspect_uljin_operation_header_only(_zip(),contract)
    with pytest.raises(ValueError,match="readable original"):
        inspect_uljin_operation_header_only(b"this is not a zip archive",PLAN)
