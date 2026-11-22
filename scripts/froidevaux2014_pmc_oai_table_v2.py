#!/usr/bin/env python3
"""Official PMC OAI-PMH full-text JATS V2 source (separate from v1 Europe PMC STOP).

Published source is already openly known; no blind ecological claim is made.
Source structure and 16 original count rows are strictly validated using v1.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
import xml.etree.ElementTree as ET

from scripts.froidevaux2014_original_vertical_table_v1 import derive

BASE="https://pmc.ncbi.nlm.nih.gov/api/oai/v1/mh/"
PARAMS={
    "verb":"GetRecord",
    "identifier":"oai:pubmedcentral.nih.gov:4278821",
    "metadataPrefix":"pmc",
}
URL=BASE+"?"+urlencode(PARAMS)

def extract_jats(data):
    root=ET.fromstring(data)
    if any(node.tag.split("}")[-1]=="error" for node in root.iter()):
        raise RuntimeError("official PMC OAI reports a source error")
    containers=[e for e in root.iter() if e.tag.split("}")[-1]=="metadata"]
    if len(containers)!=1:
        raise RuntimeError("original OAI metadata not uniquely located")
    articles=[e for e in containers[0].iter() if e.tag.split("}")[-1]=="article"]
    if len(articles)!=1:
        raise RuntimeError("original JATS fulltext article not uniquely present")
    article=articles[0]
    # Strip XML namespace tags only in the in-memory copy for the unchanged v1
    # scientific table adapter; this has no impact on numerics or weights.
    for e in article.iter():
        e.tag=e.tag.rsplit("}",1)[-1]
    xml=ET.tostring(article,encoding="utf-8")
    if b"10.1002/ece3.1296" not in xml:
        raise RuntimeError("JATS DOI does not match Froidevaux 2014")
    return xml


def main():
    output=Path("results/froidevaux2014_pmc_oai_table_v2.json")
    output.parent.mkdir(parents=True,exist_ok=True)
    try:
        with urlopen(Request(URL,headers={"User-Agent":"ODSP-bat-source-audit/1.0", "Accept":"application/xml"}),timeout=90) as r:
            data=r.read(4_000_001)
        if len(data)>4_000_000:
            raise RuntimeError("OAI response exceeded declared byte cap")
        xml=extract_jats(data)
        result=derive(xml)
        result.update({
            "retrieval":"official_NCBI_PMC_OAI_PMH_v2",
            "oai_request_url":URL,
            "oai_response_sha256":hashlib.sha256(data).hexdigest(),
            "oai_response_bytes":len(data),
            "original_fulltext_jats_sha256":hashlib.sha256(xml).hexdigest(),
            "original_first_europe_pmc_v1_result":"HTTP500_source_stop_not_replaced",
            "published_table_previously_seen_before_v2":True,
        })
    except Exception as exc:
        result={
            "status":"ncbi_original_fulltext_source_or_table_stop",
            "url":URL,
            "exception":type(exc).__name__,
            "reason":str(exc)[:350],
            "published_table_values_computed":False,
            "prior_europepmc_source_stop_remains":True,
        }
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    if result["status"]=="independent_temperate_forest_published_table_reproduced":
        print(json.dumps({
            "status":result["status"],
            "oai_response_sha256":result["oai_response_sha256"],
            "table_description":result["source_table"],
            "all16":result["all_published_labels_16"],
            "exclude_original_dominant15":result["without_original_author_removed_dominant_p_pipistrellus_15"],
            "not_a_new_site_holdout_or_true_bat_height":True,
        },indent=2))
    else:
        print(json.dumps(result,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
