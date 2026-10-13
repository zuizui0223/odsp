#!/usr/bin/env python3
"""READ-ONLY static JavaScript reconnaissance of the NIE EcoBank public ZIP link.

Never click/download, POST, bypass login, print dynamic JS arguments, expose
session tokens, print original camera coordinates, or publish animal event rows.
"""
from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json
import re

HOST = "www.nie-ecobank.kr"
URL = "https://www.nie-ecobank.kr/rdm/geodoi/selectRsrchDtaDtlVw.do?rsrchDtaId=RSD_0000000000012950"
FUNCTION = "fn_atchFileDwldOpinionModal"
MAX_BODY_BYTES = 2_000_000


class ScriptCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.srcs: list[str] = []
        self.inline_scripts: list[str] = []
        self._is_script = False
        self._current = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "script":
            return
        params = dict(attrs)
        self._is_script = True
        self._current = ""
        if params.get("src"):
            self.srcs.append(params["src"])

    def handle_data(self, data: str) -> None:
        if self._is_script:
            self._current += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._is_script:
            if self._current.strip():
                self.inline_scripts.append(self._current)
            self._current = ""
            self._is_script = False


def safe_provider_script_paths(srcs: list[str]) -> list[str]:
    out = []
    for src in srcs:
        u = urlparse(urljoin(URL, src))
        if u.scheme == "https" and u.hostname == HOST and not u.username and not u.password:
            # Discard query strings, fragments, dynamic values.
            if u.path.endswith(".js") and u.path not in out:
                out.append(u.path)
    return out


def summarize_function(text: str) -> dict[str, object]:
    """Output only code structure, never arbitrary strings/arguments."""
    declar = re.search(
        r"(?:function\s+"+re.escape(FUNCTION)+r"\s*\(|"+
        re.escape(FUNCTION)+r"\s*=\s*function\s*\(|"+
        re.escape(FUNCTION)+r"\s*:\s*function\s*\()", text)
    if not declar:
        return {"occurrence_only_no_definition": FUNCTION in text}
    excerpt = text[declar.start():declar.start()+4500]
    strings = re.findall(r"""(?:"([^"]*)"|'([^']*)')""",excerpt)
    paths = []
    for a, b in strings:
        v=(a or b).strip()
        if not v.startswith("/") or len(v)>160:
            continue
        p=urlparse(v)
        if re.fullmatch(r"/[A-Za-z0-9_./-]+",p.path) and p.path not in paths:
            paths.append(p.path)
    cleaned = re.sub(r"""(?s)"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'""", '""', excerpt)
    calls = re.findall(r"\b([A-Za-z_$][\w$]*)\s*\(",cleaned)
    allowed = {"ajax","post","get","submit","modal","dialog","location","open","download","alert","confirm","fetch","serialize","trigger","val","html","attr","action","setTimeout","show","hide"}
    common = [name for name in calls if name.lower() in allowed or name.startswith("fn_")]
    signature = re.match(r"(?:function\\s+)?"+re.escape(FUNCTION)+r"\\s*\\(([^)]*)\\)", excerpt)
    parameters = []
    if signature:
        parameters = [x.strip() for x in signature.group(1).split(",")
                      if re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", x.strip())]
    methods = re.findall(r"\\b(?:type|method)\\s*:\\s*['\\\"](GET|POST|PUT)['\\\"]", excerpt, re.I)
    # Sanitized control-flow excerpt: remove ALL quote-delimited JS literals and large numbers.
    shape = re.sub(r"\\b[0-9]{4,}\\b", "<number>", cleaned[:2700])
    return {
      "formal_parameter_NAMES_only": parameters[:10],
      "http_method_literals_near_handler": list(dict.fromkeys(methods)),
      "sanitized_control_flow_excerpt": shape[:2300],
      "function_definition_found": True,
      "static_url_path_literals_only": paths[:15],
      "public_js_call_identifiers_only": list(dict.fromkeys(common))[:25],
      "uses_ajax_keyword": bool(re.search(r"\bajax\b",cleaned,re.I)),
      "uses_post_keyword": bool(re.search(r"\bpost\b",cleaned,re.I)),
      "uses_form_keyword": bool(re.search(r"\bform\b",cleaned,re.I)),
      "uses_login_keyword": bool(re.search(r"\blogin\b",cleaned,re.I)),
    }


def analyze_html(raw: str) -> dict[str, object]:
    p=ScriptCollector()
    p.feed(raw)
    paths=safe_provider_script_paths(p.srcs)
    matches=[summarize_function(script) for script in p.inline_scripts if FUNCTION in script]
    return {
      "status": "OFFICIAL_STATIC_JS_RECON_ONLY",
      "provider_js_paths_only": paths[:45],
      "provider_js_count":len(paths),
      "inline_js_function_observations":matches[:6],
      "zip_bytes_downloaded":False,
      "forms_submitted":False,
      "source_animal_inference":False,
    }


def main() -> None:
    req=Request(URL,headers={"User-Agent":"ODSP-source-metadata-audit/1.0","Accept":"text/html"})
    try:
        with urlopen(req,timeout=16) as response:
            if urlparse(response.geturl()).hostname != HOST:
                raise ValueError("Not original official source host")
            raw=response.read(MAX_BODY_BYTES+1)
        if len(raw)>MAX_BODY_BYTES:
            raise ValueError("Page exceeds safety limit")
        result=analyze_html(raw.decode("utf-8","replace"))
    except (URLError, HTTPError, OSError, TimeoutError, ValueError) as ex:
        result={"status":"HOLD_OFFICIAL_JS_FETCH","error_class":type(ex).__name__,
                "zip_bytes_downloaded":False}
    print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2))


if __name__=="__main__":
    main()
