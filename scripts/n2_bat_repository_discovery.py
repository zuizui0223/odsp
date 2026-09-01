#!/usr/bin/env python3
"""Discover the public repository transport for the frozen N2 bat DOI.

This is a transport-only probe. It follows the selected dataset DOI and records
only landing/metadata/link structure. It does not download or inspect tracking
values and cannot make a scientific terminal decision.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "N2_BAT_STRUCTURAL_PREFLIGHT_CONTRACT.json"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.links.append(str(value))


def _request(url: str, *, method: str = "GET"):
    request = urllib.request.Request(
        url,
        method=method,
        headers={"User-Agent": "odsp-n2-bat-repository-discovery/1.0"},
    )
    return urllib.request.urlopen(request, timeout=90)


def _safe_link(url: str) -> bool:
    lowered = url.lower()
    return any(
        token in lowered
        for token in (
            "datarepository.movebank.org",
            "/handle/10255/",
            "/metadata/handle/",
            "/bitstream/handle/",
            "mets.xml",
            ".csv",
            "readme",
        )
    )


def discover() -> dict[str, object]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    doi = str(contract["source"]["movebank_repository_doi"])
    doi_url = "https://doi.org/" + doi
    try:
        with _request(doi_url) as response:
            final_url = response.geturl()
            content_type = response.headers.get("Content-Type", "")
            body = response.read(2_000_000)
    except urllib.error.HTTPError as exc:
        return {
            "discovery_status": "technical_unresolved",
            "reason": f"doi_http_status_{exc.code}",
            "doi": doi,
            "scientific_terminal_decision": False,
            "outcome_metrics_computed": False,
        }
    except urllib.error.URLError:
        return {
            "discovery_status": "technical_unresolved",
            "reason": "doi_network_error",
            "doi": doi,
            "scientific_terminal_decision": False,
            "outcome_metrics_computed": False,
        }

    links: list[str] = []
    text = ""
    if "html" in content_type.lower() or body.lstrip().lower().startswith(b"<!doctype html"):
        text = body.decode("utf-8", errors="replace")
        parser = LinkParser()
        parser.feed(text)
        for href in parser.links:
            absolute = urllib.parse.urljoin(final_url, href)
            if _safe_link(absolute):
                links.append(absolute)

    # DSpace-style repository handles expose METS metadata at a deterministic
    # path. Record the candidate URL only; fetching it is a separate step.
    mets_candidate = None
    match = re.search(r"/handle/(10255/[^/?#]+)", final_url)
    if match:
        parsed = urllib.parse.urlparse(final_url)
        mets_candidate = urllib.parse.urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                f"/metadata/handle/{match.group(1)}/mets.xml",
                "",
                "",
                "",
            )
        )

    return {
        "discovery_status": "resolved_landing",
        "doi": doi,
        "doi_url": doi_url,
        "final_url": final_url,
        "content_type": content_type,
        "repository_links": sorted(set(links)),
        "mets_candidate_url": mets_candidate,
        "body_bytes_inspected_for_links_only": len(body),
        "tracking_values_downloaded": False,
        "scientific_terminal_decision": False,
        "outcome_metrics_computed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = discover()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
