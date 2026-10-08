"""Outcome-embargoed ZIP/header structural preflight for NIE EcoBank v1.1.

This checks the provenance INPUT SHAPE, NOT animal activity or camera
uptime. In particular, no detection record and NO camera-operation
data row is opened. The ZIP directory and FIRST header line of the
camera-operation log are the only inspected contents.

The member format and thresholds are fixed in a versioned source
preflight contract, committed BEFORE any raw EcoBank file values.
Even success cannot prove original logs were independent of wildlife
images or that station-hour operating denominators exist.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import PurePosixPath
import stat
import zipfile
from typing import Any, Mapping

PROBE_ID="odsp-uljin-operation-metadata-header-preflight-v0"
OPERATION="01_core_data/camera_operation_log.csv"
EVENTS="01_core_data/cameratrap_event_records.csv"
MANIFEST="03_documentation/MANIFEST.tsv"
MAX_ARCHIVE=50_000_000
MAX_MEMBERS=100
MAX_MEMBER=100_000_000
MAX_TOTAL=200_000_000
MAX_HEADER=65_536


def _contract_guard(plan:Mapping[str,object])->Mapping[str,object]:
    if (
        not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=PROBE_ID
        or plan.get("state")!="FROZEN_BEFORE_ANY_RAW_ECOBANK_OPERATION_OR_DETECTION_RECORD_ACCESS"
    ):
        raise ValueError("unknown frozen EcoBank source preflight")
    source=plan.get("source",{})
    if (
        source.get("known_archive_download_url") is not None
        or source.get("expected_csv_member")!=OPERATION
        or source.get("forbidden_csv_member")!=EVENTS
        or source.get("expected_manifest")!=MANIFEST
    ):
        raise ValueError("EcoBank source identity/schema changed")
    p=plan.get("preflight",{})
    expected={
        "max_archive_bytes":MAX_ARCHIVE,
        "max_member_count":MAX_MEMBERS,
        "max_one_member_expanded_bytes":MAX_MEMBER,
        "max_total_expanded_bytes":MAX_TOTAL,
        "max_operation_header_line_bytes":MAX_HEADER,
        "forbid_opening_any_detection_file":True,
        "forbid_reading_operation_data_rows":True,
        "report_only_nonidentifying_file_names_and_headers":True,
    }
    if not isinstance(p,Mapping) or any(p.get(k)!=v for k,v in expected.items()):
        raise ValueError("frozen source ZIP/header security limits changed")
    return p


def _safe_path(member:zipfile.ZipInfo)->str:
    name=member.filename
    p=PurePosixPath(name)
    if (
        not name or "\\" in name or name.startswith("/")
        or any(segment in (".","..") for segment in name.split("/"))
        or ":" in name.split("/")[0]
        or stat.S_IFMT(member.external_attr>>16)==stat.S_IFLNK
        or member.flag_bits & 0x1
    ):
        raise ValueError("unsafe path/encrypted/symlink ZIP member")
    return str(p)


def inspect_uljin_operation_header_only(
    raw_zip:bytes,plan:Mapping[str,object],
)->dict[str,Any]:
    _contract_guard(plan)
    if not isinstance(raw_zip,bytes) or not 0<len(raw_zip)<=MAX_ARCHIVE:
        raise ValueError("missing/oversized original EcoBank ZIP")
    digest=hashlib.sha256(raw_zip).hexdigest()
    try:
        z=zipfile.ZipFile(io.BytesIO(raw_zip))
    except zipfile.BadZipFile as exc:
        raise ValueError("not a readable original EcoBank ZIP") from exc
    with z:
        infos=z.infolist()
        if not 0<len(infos)<=MAX_MEMBERS:
            raise ValueError("too many ZIP members")
        names=set()
        size=0
        for member in infos:
            path=_safe_path(member)
            if path in names:
                raise ValueError("duplicated ZIP member path")
            names.add(path)
            if member.file_size>MAX_MEMBER:
                raise ValueError("individual ZIP member exceeds frozen size")
            size+=member.file_size
        if size>MAX_TOTAL:
            raise ValueError("total ZIP expansion exceeds frozen size")
        if OPERATION not in names:
            raise ValueError("operation-log file missing from original package")
        if EVENTS not in names:
            raise ValueError("expected event MEMBER NAME missing; event data NOT read")
        if MANIFEST not in names:
            raise ValueError("expected manifest MEMBER NAME missing; manifest content NOT read")
        # Only one known operation CSV member is accepted. Neither the
        # outcome member nor manifest is EVER opened by this audit.
        target=z.getinfo(OPERATION)
        with z.open(target) as stream:
            first=stream.readline(MAX_HEADER+1)
        if not first or len(first)>MAX_HEADER:
            raise ValueError("operation-log header absent/exceeds frozen limit")
        try:
            header=first.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("operation-log header is not UTF8") from exc
        if header.count('"')%2:
            raise ValueError("multiline/unterminated operation header forbidden")
        parsed=list(csv.reader(io.StringIO(header),strict=True))
        if len(parsed)!=1 or not parsed[0] or any(not x.strip() for x in parsed[0]):
            raise ValueError("operation CSV header malformed")
        fields=[x.strip() for x in parsed[0]]
        if len(fields)!=len(set(fields)):
            raise ValueError("duplicate operation header field")
        # Do not GUESS operational-time granularity based on names.
        # True field origin and timestamps are not validated here.
        return {
            "schema_version":1,
            "audit_kind":PROBE_ID,
            "source_archive_sha256":digest,
            "source_archive_byte_count":len(raw_zip),
            "zip_member_count":len(infos),
            "declared_zip_uncompressed_bytes":size,
            "expected_operation_path_found":True,
            "expected_detection_path_name_found_but_not_opened":True,
            "expected_manifest_path_name_found_but_not_opened":True,
            "operation_header_sha256":hashlib.sha256(first).hexdigest(),
            "operation_header_field_count":len(fields),
            "operation_header_names":fields,
            "operation_data_rows_read":False,
            "animal_detection_member_opened":False,
            "manifest_content_read":False,
            "source_archive_version_attested":False,
            "camera_operation_metadata_originally_observation_independent_verified":False,
            "hourly_camera_uptime_or_detection_effort_verified":False,
            "paired_station_day_eligibility_verified":False,
            "primary_ecological_result_qualified":False,
            "status":"STRUCTURAL_OPERATION_HEADER_ONLY_NOT_ELIGIBLE_FOR_OUTCOME_ACCESS",
        }
