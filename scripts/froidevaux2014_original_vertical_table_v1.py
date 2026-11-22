#!/usr/bin/env python3
"""Published-source-open *descriptive* independent forest bat vertical contrast.

Froidevaux et al. 2014 primary XML Table 1: species/acoustic group counts in
forest gap, ground, canopy (with percentage columns). Exact-original-source
XML acquisition, structural count checks, two ways to calculate I(S;layer).

The raw data are pooled table cell counts, not independent plot/year events,
not per-bat flight height and not detection-calibrated latent use.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.request import Request,urlopen
import xml.etree.ElementTree as ET

DOI="10.1002/ece3.1296"
PMC="PMC4278821"
URL="https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4278821/fullTextXML"
EXPECTED_ROWS=16
EXPECTED_SUMS={"gap":52547,"ground":41850,"canopy":35630}
EXPECTED_ALL=130027
DOMINANT="pipistrellus pipistrellus"

def get():
    req=Request(URL,headers={"User-Agent":"ODSP-Froidevaux-original-table/1.0",
                              "Accept":"application/xml,text/xml,*/*"})
    with urlopen(req,timeout=180) as response:
        data=response.read(4_000_001)
    if len(data)<10000 or len(data)>4_000_000:
        raise RuntimeError("original XML bytes outside anticipated bounds")
    return data

def text(node):
    return " ".join("".join(node.itertext()).split())

def numeric(raw):
    src=raw.replace(",","").replace(" ","").strip()
    if not re.fullmatch(r"[0-9]+",src):
        raise ValueError("source numerical count is not an integer")
    return int(src)

def parse_primary_table(xml_bytes):
    root=ET.fromstring(xml_bytes)
    options=[]
    for tw in root.findall(".//table-wrap"):
        cap=tw.find("caption")
        name=text(cap).lower() if cap is not None else ""
        if "number of sequences" in name and "microhabitat" in name:
            options.append(tw)
    if len(options)!=1:
        raise RuntimeError(f"original Table 1 not uniquely identified: {len(options)} candidates")
    table=options[0].find(".//table")
    if table is None:raise RuntimeError("table-wrap has no encoded numeric table")
    trs=table.findall(".//tbody/tr")
    if not trs:
        raise RuntimeError("missing tbody/tr")
    out=[]
    total_from_source=None
    for tr in trs:
        cols=[text(c) for c in tr if c.tag.split("}")[-1] in ("td","th")]
        if not cols:continue
        row_name=cols[0].strip()
        if row_name.lower()=="total":
            # The source Total row has only 3 layer counts; it is checked from
            # the original 16 taxa sums, not trusted for inference.
            total_from_source=cols
            continue
        if len(cols)<9:
            raise RuntimeError(f"source published count/percent table unexpectedly has {len(cols)} cells")
        # Source order: Taxon, Guild, Gap (No.,%), Ground (No.,%),
        # Canopy (No.,%), Total (No.,%).
        gap,ground,canopy,total=map(numeric,(cols[2],cols[4],cols[6],cols[8]))
        if total!=gap+ground+canopy:
            raise RuntimeError(f"original table does not reconcile for one taxon")
        out.append({"taxon":row_name,"guild":cols[1].strip(),
                    "gap":gap,"ground":ground,"canopy":canopy,"total":total})
    if len(out)!=EXPECTED_ROWS:
        raise RuntimeError(f"expected 16 original taxa, parsed {len(out)}")
    if len({r["taxon"] for r in out})!=EXPECTED_ROWS:
        raise RuntimeError("duplicate published taxon names")
    for habitat,n in EXPECTED_SUMS.items():
        if sum(r[habitat] for r in out)!=n:
            raise RuntimeError(f"original {habitat} published count total mismatch")
    if sum(r["total"] for r in out)!=EXPECTED_ALL:
        raise RuntimeError("original published Table 1 grand total mismatch")
    if sum(1 for r in out if " ".join(r["taxon"].lower().split())==DOMINANT)!=1:
        raise RuntimeError("original predeclared dominance taxon could not be found once")
    return out,{"table_caption":text(options[0].find("caption")),
                "source_tbody_row_count":len(trs),
                "total_source_row_was_detected":total_from_source is not None}

def metrics(table):
    total=sum(a+b for a,b in table)
    if total<=0:
        raise ValueError("must have nonzero original acoustic sequences")
    layer_ground=sum(a for a,_ in table)
    layer_canopy=sum(b for _,b in table)
    pground=layer_ground/total
    pcanopy=layer_canopy/total
    hb=-math.fsum(p*math.log(p) for p in (pground,pcanopy) if p>0)
    info=0.0
    conditional_h=0.0
    for a,b in table:
        s=a+b
        if s==0:continue
        for value,globalprob in ((a,pground),(b,pcanopy)):
            if value>0:
                p=value/total
                info+=p*math.log((value/s)/globalprob)
        for value in (a,b):
            if value>0:
                v=value/s
                conditional_h-=(s/total)*v*math.log(v)
    if abs(info-(hb-conditional_h))>1e-12:
        raise RuntimeError("entropy identity mismatch")
    return {
        "ground_source_sequences":layer_ground,
        "canopy_source_sequences":layer_canopy,
        "ground_plus_canopy_sequences":total,
        "observed_label_stratum_information_nats":max(0.,info),
        "observed_recording_stratum_entropy_nats":hb,
        "observed_label_information_fraction_of_stratum_entropy":max(0.,info)/hb,
        "conditional_stratum_entropy_given_label_nats":conditional_h,
        "independent_information_identity_reconciliation_abs":abs(info-(hb-conditional_h)),
        "label_count":len(table),
        "binary_stratum_detector":True,
    }

def derive(xml_bytes):
    entries,source=parse_primary_table(xml_bytes)
    source_table=[(r["ground"],r["canopy"]) for r in entries]
    without_dominant=[(r["ground"],r["canopy"]) for r in entries
                      if " ".join(r["taxon"].lower().split())!=DOMINANT]
    return {
        "status":"independent_temperate_forest_published_table_reproduced",
        "source_title":"Optimizing passive acoustic sampling of bats in forests",
        "publication_doi":DOI,
        "pmc":PMC,
        "fulltext_xml_url":URL,
        "original_xml_sha256":hashlib.sha256(xml_bytes).hexdigest(),
        "original_xml_bytes":len(xml_bytes),
        "source_table":source,
        "published_microhabitat_counts":[
            {"taxon":r["taxon"],"guild":r["guild"],"forest_gap":r["gap"],
             "forest_ground":r["ground"],"forest_canopy":r["canopy"]} for r in entries
        ],
        "all_published_labels_16":metrics(source_table),
        "without_original_author_removed_dominant_p_pipistrellus_15":metrics(without_dominant),
        "independent_site_or_night_holdout_available":False,
        "this_work_is_blinded_to_original_table_outcomes":False,
        "actual_animal_vertical_flight_height_recorded":False,
        "species_or_microphone_detection_q_calibrated":False,
        "field_geographic_generalization_inferred":False,
    }

def main():
    dst=Path("results/froidevaux_2014_original_stratum_table_v1.json")
    dst.parent.mkdir(parents=True,exist_ok=True)
    try:
        receipt=derive(get())
    except Exception as exc:
        receipt={
            "status":"original_source_access_or_table_schema_stop",
            "source":URL,
            "reason":str(exc)[:300],
            "exception":type(exc).__name__,
            "real_table_effects_estimated":False,
        }
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    if receipt["status"]=="independent_temperate_forest_published_table_reproduced":
        print(json.dumps({
            "status":receipt["status"],"xml_sha256":receipt["original_xml_sha256"],
            "source_table":receipt["source_table"],
            "all_16":receipt["all_published_labels_16"],
            "without_dominant_15":receipt["without_original_author_removed_dominant_p_pipistrellus_15"],
            "is_original_publication_descriptive_only":True,
        },indent=2))
    else:print(json.dumps(receipt,indent=2))
    # A source gate stop is not a software failure; no fabricated observations.
    return 0

if __name__=="__main__":
    raise SystemExit(main())
