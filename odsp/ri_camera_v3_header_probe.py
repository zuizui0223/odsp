"""Pinned Rhode Island camera survey v3 CSV HEADER-ONLY source recovery.

This post-failure technical probe reads no species records, timestamps, or
deployment values. It is NOT an untouched external pre-outcome claim: the
prior v0 workflow already parsed rows internally before failing to align
site/camera identities. Its narrow output can inform a NEW exploratory,
explicitly post-schema-exposure analysis, never retroactively repair v0.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import PurePosixPath
import zipfile
from typing import Mapping, Any

from .ri_zipinfo_technical_recovery_v0 import (
    SOURCE_MD5, MAX_ARCHIVE, REQUIRED_CSV_BASENAMES,
    inspect_ri_pinned_zip_central_directory,
)

PROBE_ID = "odsp-ri-camera-v3-header-only-recovery-v0"
MAX_HEADER_BYTES=65536


def _normalized(name: str) -> str:
    return "".join(x for x in name.casefold() if x.isascii() and x.isalnum())


def inspect_camera_archive_headers_only(
    raw: bytes, plan: Mapping[str,object],
    original_aliases: Mapping[str, list[str]],
) -> dict[str,Any]:
    """Return headers/ambiguity only; never read a data record."""
    if plan.get("contract_id")!=PROBE_ID or plan.get("max_header_line_bytes")!=MAX_HEADER_BYTES:
        raise ValueError("schema-probe freeze identity mismatch")
    if plan.get("source",{}).get("md5")!=SOURCE_MD5:
        raise ValueError("source identity differs from header-probe freeze")
    if set(plan.get("source",{}).get("allowed_members",[]))!=REQUIRED_CSV_BASENAMES:
        raise ValueError("expected member list differs from frozen two members")
    # Structure gate reads ZIP central directory only, before opening members.
    scan=inspect_ri_pinned_zip_central_directory(raw)
    by_basename={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for item in z.infolist():
            if item.is_dir(): continue
            name=PurePosixPath(item.filename).name
            if name not in REQUIRED_CSV_BASENAMES: continue
            with z.open(item) as member:
                first_line=member.readline(MAX_HEADER_BYTES+1)
            if not first_line or len(first_line)>MAX_HEADER_BYTES:
                raise ValueError("header missing or exceeds frozen header-only byte cap")
            try:
                header=first_line.decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                raise ValueError("header is not UTF-8; encoding guess forbidden") from exc
            # CSV embedded newline/quoting in a header is not admissible
            # under this one-line-only contract. Avoid reading next row.
            if header.count('"') % 2:
                raise ValueError("unterminated quoted header; no row values opened")
            parsed=list(csv.reader(io.StringIO(header,newline=""),strict=True))
            if len(parsed)!=1 or not parsed[0] or any(not x.strip() for x in parsed[0]):
                raise ValueError("invalid one-line source CSV header")
            fields=tuple(x.strip() for x in parsed[0])
            if len(set(fields))!=len(fields):
                raise ValueError("duplicate exact header labels")
            normalized=[_normalized(x) for x in fields]
            if len(normalized)!=len(set(normalized)):
                raise ValueError("duplicate normalized header names")
            matches={}
            for role,aliases in original_aliases.items():
                permitted={_normalized(x) for x in aliases}
                found=sorted(field for field in fields if _normalized(field) in permitted)
                matches[role]={
                    "original_frozen_alias_match_count":len(found),
                    "matches":found,
                    "mapping_authorized":len(found)==1,
                }
            by_basename[name]={
                "header_field_count":len(fields),
                "header_names":list(fields),
                "header_line_sha256":hashlib.sha256(first_line).hexdigest(),
                "first_record_value_bytes_read":False,
                "frozen_alias_diagnostics":matches,
            }
    if set(by_basename)!=REQUIRED_CSV_BASENAMES:
        raise ValueError("source header coverage incomplete")
    return {
        "schema_version":1,
        "probe_id":PROBE_ID,
        "source_archive_md5_verified":scan.archive_md5_verified,
        "pinned_source_archive_md5":SOURCE_MD5,
        "source_zip_member_count":scan.member_count,
        "source_headers":by_basename,
        "source_data_row_values_read_by_this_probe":False,
        "source_data_row_values_may_have_been_read_by_prior_v0_workflow":True,
        "original_v0_frozen_source_aliases_amended":False,
        "heldout_scores_computed":False,
        "empirical_primary_qualified":False,
        "next_step":"New post-schema-exposure exploratory contract or terminal source stop, NOT v0 pre-outcome reclassification",
    }
