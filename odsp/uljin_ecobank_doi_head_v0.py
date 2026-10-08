"""HEAD-only EcoBank DOI availability check; ZERO response/event log bytes read.

New source needs separate operator effort logs before any animal outcome
sampling/score model. Even a successful HEAD request cannot attest a
source-file hash, original maintenance log, clock-hour exposure or an
independent sample of Uljin physical stations.

Only the exact public DOI is requested, every HTTPS redirect host is
checked BEFORE the next HEAD, and redirects never switch to GET.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable,Mapping,Any
from urllib.parse import urljoin,urlsplit

PROBE_ID="uljin-ecobank-doi-http-head-only-v0"
DOI="https://doi.org/10.22756/ETC.20260000001022"
ALLOW=frozenset(("doi.org","www.nie-ecobank.kr","nie-ecobank.kr"))
REDIRECT_CODES=frozenset((301,302,303,307,308))


def validate_plan(plan:Mapping[str,object])->None:
    if (not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("probe_id")!=PROBE_ID
        or plan.get("status")!="POST_ASTRONOMY_DESIGN_PRE_SOURCE_CONTENT_ACCESS"
        or plan.get("only_requested_uri")!=DOI
        or plan.get("allowed_redirect_hosts")!=sorted(ALLOW)
        or plan.get("allowed_methods")!=["HEAD"]
        or plan.get("http_body_bytes_read")!=0
        or plan.get("allow_GET") is not False
        or plan.get("max_redirects")!=5):
        raise ValueError("unrecognized frozen HEAD-only source prospectivity contract")


def _public_uri(uri:str)->tuple[str,str]:
    parts=urlsplit(uri)
    if (
        parts.scheme!="https" or parts.hostname not in ALLOW
        or parts.username is not None or parts.password is not None
        or not parts.path.startswith("/")
    ):
        raise ValueError("DOI redirect outside predeclared allowed HTTPS hosts")
    return parts.hostname,parts.path


def probe_head_only(
    plan:Mapping[str,object],
    *,
    request_head:Callable[[str],tuple[int,Mapping[str,str]]],
)->dict[str,Any]:
    """Call injected HEAD service only; never inspect/accept HTTP bodies."""
    validate_plan(plan)
    target=DOI
    redirects=0
    status=0
    content_type=""
    length=None
    while True:
        host,path=_public_uri(target)
        status,headers=request_head(target)
        if isinstance(status,bool) or not isinstance(status,int) or status<100 or status>599:
            raise ValueError("invalid HEAD status")
        if not isinstance(headers,Mapping):
            raise ValueError("HEAD response metadata is not a mapping")
        normalized={str(k).lower():str(v).strip() for k,v in headers.items()}
        if status in REDIRECT_CODES:
            location=normalized.get("location","")
            if not location or redirects>=5:
                raise ValueError("HEAD redirect missing location or exceeds cap")
            candidate=urljoin(target,location)
            _public_uri(candidate)
            target=candidate
            redirects+=1
            continue
        content_type=normalized.get("content-type","").split(";")[0].lower()
        length_raw=normalized.get("content-length")
        if length_raw is not None and length_raw.isdecimal():
            length=int(length_raw)
        break
    if status!=200:
        kind="SOURCE_ACCESS_UNVERIFIED_NO_FALLBACK"
    elif content_type in ("text/html","application/xhtml+xml"):
        kind="DOI_LANDING_PAGE_ONLY_NO_SOURCE_BYTES"
    elif content_type in (
        "application/zip","application/x-zip-compressed",
        "application/octet-stream"
    ):
        kind="HEADER_SUGGESTS_ARCHIVE_BUT_FILE_CONTENT_NOT_VERIFIED"
    else:
        kind="DOI_HEAD_RETURNED_UNCLASSIFIED_CONTENT_TYPE"
    return {
        "schema_version":1,
        "probe_id":PROBE_ID,
        "status":kind,
        "http_status":status,
        "final_https_host":host,
        "final_https_path_without_query":path,
        "redirect_count":redirects,
        "content_type":content_type,
        "content_length_header_or_null":length,
        "http_request_methods_used":["HEAD"],
        "http_body_bytes_read":0,
        "any_animal_detection_or_camera_operation_rows_read":False,
        "original_camera_operation_log_provenance_verified":False,
        "hourly_camera_uptime_verified":False,
        "data_archive_hash_verified":False,
        "positive_hysteresis_effect_tested":False,
        "qualified_ODSP_external_validation_registered":False,
        "prior_RI_ecological_analyses_reclassified":False,
    }
