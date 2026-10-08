"""Only synthetic HEAD response metadata; never open any website in tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.uljin_ecobank_doi_head_v0 import probe_head_only

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_ECOBANK_DOI_HEAD_PROBE_V0_CONTRACT.json"
DOI="https://doi.org/10.22756/ETC.20260000001022"


def frozen():
    return json.loads(PLAN.read_text())


def test_allowed_https_head_redirect_to_only_website_is_not_archive_admission():
    requests=[]
    def request(uri):
        requests.append(uri)
        if uri==DOI:
            return 302,{"Location":"https://www.nie-ecobank.kr/dataset/123?session=REDACT"}
        return 200,{"Content-Type":"text/html; charset=UTF-8","Content-Length":"8000"}
    out=probe_head_only(frozen(),request_head=request)
    assert out["status"]=="DOI_LANDING_PAGE_ONLY_NO_SOURCE_BYTES"
    assert out["final_https_host"]=="www.nie-ecobank.kr"
    assert out["final_https_path_without_query"]=="/dataset/123"
    assert out["http_status"]==200
    assert out["redirect_count"]==1
    assert out["http_request_methods_used"]==["HEAD"]
    assert out["http_body_bytes_read"]==0
    assert len(requests)==2
    assert not out["original_camera_operation_log_provenance_verified"]
    assert not out["data_archive_hash_verified"]
    assert not out["qualified_ODSP_external_validation_registered"]
    assert "REDACT" not in json.dumps(out)


def test_untrusted_redirect_never_follows():
    requests=[]
    def request(uri):
        requests.append(uri)
        return 302,{"Location":"https://attacker.example/secret.csv"}
    with pytest.raises(ValueError,match="allowed HTTPS hosts"):
        probe_head_only(frozen(),request_head=request)
    assert requests==[DOI]


@pytest.mark.parametrize("location",[
    "http://www.nie-ecobank.kr/file.zip",
    "https://other.nie-ecobank.kr/file.zip",
    "https://doi.org@attacker.example/file",
])
def test_non_https_or_unlisted_domain_fails_closed(location):
    with pytest.raises(ValueError,match="allowed HTTPS"):
        probe_head_only(
            frozen(),
            request_head=lambda uri:(301,{"Location":location}),
        )


def test_405_head_is_source_unavailable_no_get_fallback():
    log=[]
    def request(uri):
        log.append(uri)
        return 405,{"Content-Type":"text/html"}
    out=probe_head_only(frozen(),request_head=request)
    assert out["status"]=="SOURCE_ACCESS_UNVERIFIED_NO_FALLBACK"
    assert len(log)==1
    assert not out["hourly_camera_uptime_verified"]


def test_archive_head_does_not_assert_actual_data_available():
    out=probe_head_only(
        frozen(),
        request_head=lambda uri:(
            200,{"Content-Type":"application/zip","Content-Length":"24000"}
        ),
    )
    assert out["status"]=="HEADER_SUGGESTS_ARCHIVE_BUT_FILE_CONTENT_NOT_VERIFIED"
    assert out["content_length_header_or_null"]==24000
    assert out["http_body_bytes_read"]==0
    assert not out["data_archive_hash_verified"]


def test_allowlist_contract_and_http_method_cannot_be_modified():
    p=frozen()
    p["allow_GET"]=True
    with pytest.raises(ValueError,match="HEAD-only"):
        probe_head_only(p,request_head=lambda uri:(200,{}))
    p=frozen()
    p["allowed_redirect_hosts"].append("attacker.example")
    with pytest.raises(ValueError,match="HEAD-only"):
        probe_head_only(p,request_head=lambda uri:(200,{}))
