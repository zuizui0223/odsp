#!/usr/bin/env python3
"""Read-only public provider-source receipt; no biological outcomes or credentials.

The official landing's listed ZIP size/name are not proof of byte authenticity.
This one-shot route never writes/prints event rows or camera coordinates.
"""
from __future__ import annotations

from html import unescape
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

RECORD_ID = "RSD_0000000000012950"
URL = (
    "https://www.nie-ecobank.kr/rdm/geodoi/selectRsrchDtaDtlVw.do"
    f"?rsrchDtaId={RECORD_ID}"
)
FILENAME = "Uljin_camera_trap_ungulates_public_dataset_v1.1_20260305_EcoBank_revised.zip"
HOST = "www.nie-ecobank.kr"
VERSION = "1.1"
TIMEOUT_SECONDS = 18
MAX_HTML_BYTES = 2_000_000


def _attestation_url(target: str) -> bool:
    p = urlparse(target)
    return p.scheme == "https" and p.hostname == HOST and not p.username and not p.password


def _extract_relevant_markup(page: str) -> tuple[bool, list[dict[str, str]]]:
    """Inspect public file control semantics, not the page's tokens or private metadata."""
    location = page.find(FILENAME)
    if location < 0:
        return False, []
    excerpt = page[max(0, location - 2400): location + 1400]
    candidates = []
    for tag in re.findall(r"<(?:a|button|input)\b[^>]*>", excerpt, re.I | re.S):
        result: dict[str, str] = {}
        for key in ("href", "onclick", "download"):
            match = re.search(rf"\b{key}\s*=\s*([\"'])(.*?)\1", tag, re.I | re.S)
            if not match:
                continue
            value = unescape(match.group(2).strip())
            if key == "onclick":
                fn = re.search(r"\b([A-Za-z_$][A-Za-z0-9_$]*)\s*\(", value)
                if fn:
                    result["onclick_function_name_only"] = fn.group(1)
            elif key == "href":
                if not value.lower().startswith(("javascript:", "#")):
                    abs_url = urljoin(URL, value)
                    if _attestation_url(abs_url) and re.search(r"download|file|\.zip", urlparse(abs_url).path, re.I):
                        # Do not include query parameters: could include ephemeral tokens.
                        result["same_origin_download_path_candidate"] = urlparse(abs_url).path
            elif key == "download":
                result["download_attribute_present"] = "true"
        if result and result not in candidates:
            candidates.append(result)
    return True, candidates[:12]


def _nearby_tag_signatures(page: str) -> list[dict[str, object]]:
    """Only print tag/attribute NAMES; never expose HTML values or request tokens."""
    location = page.find(FILENAME)
    if location < 0:
        return []
    excerpt = page[max(0, location - 850):location + 700]
    signatures = []
    for match in re.finditer(r"<\s*([A-Za-z][\w-]*)\b([^>]*)>", excerpt, re.I | re.S):
        tagname, fields = match.groups()
        if tagname.lower() not in ("a", "button", "input", "span", "div", "li", "p", "i"):
            continue
        names = re.findall(r"\s([A-Za-z_:][A-Za-z0-9_:.-]*)\s*=", fields)
        signature: dict[str, object] = {
            "tag": tagname.lower(),
            "attribute_names_only": sorted(set(names)),
        }
        onclick = re.search(r"\bonclick\s*=\s*([\"'])(.*?)\1", fields, re.I | re.S)
        if onclick:
            name = re.search(r"\b([A-Za-z_$][A-Za-z0-9_$]*)\s*\(", unescape(onclick.group(2)))
            if name:
                signature["onclick_function_only"] = name.group(1)
        signatures.append(signature)
    return signatures[:18]


def inspect_page_bytes(data: bytes, *, final_url: str) -> dict[str, object]:
    if not _attestation_url(final_url):
        return {"status": "HOLD_NON_OFFICIAL_FINAL_URL", "official_origin": False}
    page = data.decode("utf-8", "replace")
    found, elements = _extract_relevant_markup(page)
    version_in_page = bool(re.search(r">\s*1\.1\s*<", page))
    result: dict[str, object] = {
        "status": "OFFICIAL_LANDING_ZIP_LISTED_BYTES_NOT_DOWNLOADED" if found else "HOLD_OFFICIAL_LANDING_ZIP_NAME_NOT_FOUND",
        "official_origin": True,
        "record_id": RECORD_ID,
        "portal_visible_v1p1_zip_filename": FILENAME if found else None,
        "portal_version_history_mentions_v1p1": version_in_page,
        "download_controls_redacted": elements,
        "nearby_html_tag_attribute_names_only": _nearby_tag_signatures(page),
        "original_zip_bytes_read": False,
        "independent_sha256_attested": False,
        "raw_camera_events_or_operation_hours_read": False,
        "biological_effect_computed": False,
    }
    return result


def main() -> None:
    request = Request(URL, headers={"User-Agent": "ODSP-research-source-metadata-check/1.0 (+GitHub-project)",
                                    "Accept": "text/html,application/xhtml+xml"})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as reply:
            status = reply.status
            destination = reply.geturl()
            body = reply.read(MAX_HTML_BYTES + 1)
        if len(body) > MAX_HTML_BYTES:
            output = {"status": "HOLD_PAGE_HTML_TOO_LARGE"}
        elif status != 200:
            output = {"status": "HOLD_OFFICIAL_SITE_NOT_HTTP_200", "http_status": status}
        else:
            output = inspect_page_bytes(body, final_url=destination)
            output["http_status"] = status
        print(json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True))
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        print(json.dumps({
            "status": "HOLD_OFFICIAL_SOURCE_LANDING_NETWORK_UNAVAILABLE",
            "error_class": type(exc).__name__,
            "original_zip_bytes_read": False,
            "biological_effect_computed": False,
        }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
