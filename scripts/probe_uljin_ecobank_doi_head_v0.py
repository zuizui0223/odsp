#!/usr/bin/env python3
"""Source discovery by bounded HEAD metadata alone, no wildlife or log content.

When a DOI resolves to HTML, do not parse that HTML or invent an archive
URL. When it fails, report SOURCE_ACCESS_UNVERIFIED_NO_FALLBACK. This
is deliberately NOT a way to obtain EcoBank animal records.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

from odsp.uljin_ecobank_doi_head_v0 import probe_head_only

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_ECOBANK_DOI_HEAD_PROBE_V0_CONTRACT.json"
OUTPUT=ROOT/"ULJIN_ECOBANK_DOI_HEAD_V0_FIRST_RECEIPT.json"


class NoAutoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        # The scientific probe itself validates each redirect target
        # BEFORE any new HEAD request, never exposing source file bytes.
        return None


OPENER=urllib.request.build_opener(NoAutoRedirect)


def request_head_only(uri:str)->tuple[int,dict[str,str]]:
    request=urllib.request.Request(
        uri,method="HEAD",
        headers={
            "User-Agent":"ODSP/0.11 Korean EcoBank frozen source HEAD only",
            "Accept":"*/*",
        },
    )
    if request.get_method()!="HEAD":
        raise ValueError("only HEAD requests are permitted")
    try:
        with OPENER.open(request,timeout=30) as response:
            return int(response.status),dict(response.headers.items())
    except urllib.error.HTTPError as exc:
        # Includes 3xx because auto redirects are disabled.
        # DO NOT call .read() even on HTTP errors/redirects.
        return int(exc.code),dict(exc.headers.items())


def main()->int:
    frozen=PLAN.read_bytes()
    plan=json.loads(frozen)
    base={
        "schema_version":1,
        "frozen_probe_contract_sha256":hashlib.sha256(frozen).hexdigest(),
        "first_probe_request_method":"HEAD",
        "raw_camera_operation_log_bytes_read":False,
        "wildlife_detection_rows_accessed":False,
        "original_Korean_archive_downloaded":False,
        "camera_hourly_exposure_proven":False,
        "new_external_ODSP_ecology_registered":False,
    }
    try:
        record=probe_head_only(plan,request_head=request_head_only)
        report={**base,**record}
        rc=0 if record["http_status"]==200 else 2
    except Exception as exc:
        report={
            **base,
            "status":"SOURCE_ACCESS_UNVERIFIED_NO_FALLBACK",
            "error_type":type(exc).__name__,
            "error_reason":str(exc)[:240],
            "redirect_allowlist_failed_or_source_unreachable":True,
        }
        rc=2
    OUTPUT.write_text(
        json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+"\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status":report["status"],
        "host":report.get("final_https_host"),
        "http_status":report.get("http_status"),
        "redirect_count":report.get("redirect_count"),
        "any_body_read":False,
        "receipt":OUTPUT.name,
    },sort_keys=True),flush=True)
    return rc


if __name__=="__main__":
    raise SystemExit(main())
