#!/usr/bin/env python3
"""Public article-abstract cross-landscape EVIDENCE, not a pooled meta-analysis.

Re-check the *two Korean journal KCI public abstracts* against their original
published DOI, and the genuine MD5-attested 2026 Zenodo Uljin supplementary
whole-period counts. Only retain descriptive night-share percentages and
within-publication species comparisons. Never synthesize event-level
observations, claim a matching day/night definition or compute a p-value.
"""
from __future__ import annotations

import argparse
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from inspect_uljin_published_supp3_aggregate_v0 import download as get_uljin_supp3
from run_uljin_published_supp3_daypart_signatures_v0 import evaluate as read_uljin

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_INDEPENDENT_KOREAN_UNGULATE_CONTEXT_V0_CONTRACT.json"
ULJIN_PLAN=ROOT/"ULJIN_PUBLISHED_SUPPL3_DAYPART_SIGNATURE_V0_CONTRACT.json"
MAX_PUBLIC_HTML_BYTES=2_500_000
SOURCE_HOST="www.kci.go.kr"
STATUS="SOURCE_VERIFIED_NONHARMONIZED_KOREAN_CROSS_STUDY_ECOLOGICAL_CONTEXT"

class PublicText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.excluded=0
        self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style"):
            self.excluded+=1
    def handle_endtag(self,tag):
        if tag in ("script","style"):
            self.excluded=max(0,self.excluded-1)
    def handle_data(self,data):
        if not self.excluded:
            self.parts.append(data)

def html_plain(html_text:str)->str:
    p=PublicText()
    p.feed(html_text)
    return " ".join(unescape(" ".join(p.parts)).split())

def official_kci_get(url:str)->str:
    parsed=urlparse(url)
    if parsed.scheme!="https" or parsed.hostname!=SOURCE_HOST:
        raise ValueError("HOLD_KCI_URL_UNEXPECTED_HOST")
    request=Request(url,headers={"User-Agent":"ODSP-public-research-metadata/1.0",
                                 "Accept":"text/html"})
    with urlopen(request,timeout=24) as response:
        final=urlparse(response.geturl())
        if final.scheme!="https" or final.hostname!=SOURCE_HOST:
            raise ValueError("HOLD_KCI_REDIRECT_OUTSIDE_PUBLISHER")
        content=response.read(MAX_PUBLIC_HTML_BYTES+1)
    if len(content)>MAX_PUBLIC_HTML_BYTES:
        raise ValueError("HOLD_KCI_OVERSIZED_HTML")
    return content.decode("utf-8","replace")

def verify_abstract(html_text:str,reference:dict,case:str)->dict:
    if reference["doi"] not in html_text:
        raise ValueError("HOLD_DOI_ABSENT_ORIGINAL_JOURNAL_PAGE")
    plain=html_plain(html_text)
    lower=plain.lower()
    if case=="suburban_2024":
        anchor="this study aimed to figure out diel activity patterns of water deer and wild boar"
        must_include=("18 camera traps", "january 2021 to november 2022",
                      "dawn, day, dusk, and night","fall and winter")
        perc=reference["night_fraction_pct"] | reference["published_trail_day_pct"]
    elif case=="bukhansan_2025":
        anchor="the objective of this study was to investigate the daily activity patterns"
        must_include=("bukhansan national park", "457 images", "forests", "wetlands")
        perc=reference["night_fraction_pct"]
    else:
        raise ValueError("HOLD_UNKNOWN_PUBLIC_RESEARCH_CASE")
    offset=lower.find(anchor)
    if offset<0:
        raise ValueError("HOLD_EXPECTED_PUBLIC_ABSTRACT_MISSING")
    excerpt=lower[offset:offset+4500]
    for token in must_include:
        if token not in excerpt:
            raise ValueError("HOLD_PUBLIC_ABSTRACT_DESIGN_NOT_GROUNDED_"+re.sub(r"\W+","_",token))
    # Check as numeric percentages: 78 and 78.0 are the same
    # published percentage, despite JSON serialization of a terminal .0.
    published_percentages = [
        float(v) for v in re.findall(r"(?<![\d.])(\d+(?:\.\d+)?)\s*%", excerpt)
    ]
    for key,val in perc.items():
        if not any(abs(v-float(val))<1e-9 for v in published_percentages):
            raise ValueError("HOLD_EXPECTED_PUBLISHED_PERCENT_NOT_IN_ABSTRACT_"+key)
    return {"doi":reference["doi"],
            "public_source_verified":True,
            "verified_abstract_percentages":perc,
            "raw_station_event_rows_read":False,
            "independent_source_camera_hours_checked":False}

def compare(contract:dict,uljin:dict,han_html:str,jeong_html:str)->dict:
    if (contract.get("schema_version")!=1
        or contract.get("contract_id")!="uljin_public_independent_korean_context_comparison_v0"
        or contract.get("analysis_stage")!="POST_PUBLICATION_TARGETED_ECOLOGICAL_CONTEXT_NOT_PREREGISTERED"
        or any(x is not False for x in contract.get("integrity_guards",{}).values())
        or len(contract.get("integrity_guards",{}))!=11):
        raise ValueError("HOLD_CROSS_STUDY_INFERENCE_BOUNDARY")
    if (uljin.get("status")!="REPRODUCED_PUBLISHED_DAYPART_POOLED_DESCRIPTIVE_SIGNATURE_ONLY"
        or uljin.get("reproduced_total_events")!=4623
        or uljin.get("original_hourly_camera_operation_verified") is not False):
        raise ValueError("HOLD_ULJIN_ORIGINAL_SOURCE_NOT_ALLOWED")
    verified_han=verify_abstract(han_html,contract["sources"]["suburban_2024"],"suburban_2024")
    verified_jeong=verify_abstract(jeong_html,contract["sources"]["bukhansan_2025"],"bukhansan_2025")
    props={s["species"]:s["period_counts"] for s in uljin["species_profiles"]}
    if set(props)!={"Long-tailed goral","Siberian roe deer","Water deer","Wild boar"}:
        raise ValueError("HOLD_ULJIN_FOUR_TAXA_NOT_AVAILABLE")
    u=props["Water deer"]
    b=props["Wild boar"]
    u_n=100*u["nighttime"]/sum(u.values())
    b_n=100*b["nighttime"]/sum(b.values())
    if not (60<u_n<62 and 24<b_n<26):
        raise ValueError("HOLD_REAL_ULJIN_NIGHT_COUNTS_INCONSISTENT")
    han=verified_han["verified_abstract_percentages"]
    jeong=verified_jeong["verified_abstract_percentages"]
    # Same-study measurements first; NO between-study estimands.
    contexts=[
      {"study":"Jeon_Lim_2026_Uljin",
       "stratum":"all_published_dates_pooled",
       "species_night_percent":{"Water deer":round(u_n,6),"Wild boar":round(b_n,6)},
       "water_minus_boar_percentage_points":round(u_n-b_n,6),
       "night_category":"night outside civil twilight",
       "sampling":"independent-events pooled full year",
       "season_matched_to_other_studies":False},
      {"study":"Han_et_al_2024_suburban",
       "stratum":"autumn",
       "species_night_percent":{"Water deer":han["water_deer_fall"],"Wild boar":han["wild_boar_fall"]},
       "water_minus_boar_percentage_points":round(han["water_deer_fall"]-han["wild_boar_fall"],6),
       "night_category":"night within separate dawn/day/dusk/night classification",
       "sampling":"published seasonal camera-photo rate shares",
       "season_matched_to_other_studies":False},
      {"study":"Jeong_et_al_2025_Bukhansan",
       "stratum":"forest",
       "species_night_percent":{"Water deer":jeong["water_deer_forest"],"Wild boar":jeong["wild_boar_forest"]},
       "water_minus_boar_percentage_points":round(jeong["water_deer_forest"]-jeong["wild_boar_forest"],6),
       "night_category":"binary day versus night in source publication",
       "sampling":"published habitat-level camera images",
       "season_matched_to_other_studies":False},
      {"study":"Jeong_et_al_2025_Bukhansan",
       "stratum":"wetland",
       "species_night_percent":{"Water deer":jeong["water_deer_wetland"],"Wild boar":jeong["wild_boar_wetland"]},
       "water_minus_boar_percentage_points":round(jeong["water_deer_wetland"]-jeong["wild_boar_wetland"],6),
       "night_category":"binary day versus night in source publication",
       "sampling":"published habitat-level camera images",
       "season_matched_to_other_studies":False}
    ]
    assert len(contexts)==4
    return {
      "status":STATUS,
      "sources_rechecked":["10.3897/BDJ.14.e191556.suppl3",
                           verified_han["doi"],verified_jeong["doi"]],
      "suburban_2024_18_camera_trap_public_abstract_verified":True,
      "bukhansan_2025_457_analyzed_images_public_abstract_verified":True,
      "within_study_season_and_habitat_night_percent_contexts":contexts,
      "reported_night_share_ordering_not_universal_across_contexts":
           any(x["water_minus_boar_percentage_points"]<0 for x in contexts) and
           any(x["water_minus_boar_percentage_points"]>0 for x in contexts),
      "han_suburban_wild_boar_winter_night_percent":han["wild_boar_winter"],
      "han_suburban_trail_near_far_day_percent":{
        k:han[k] for k in ("water_deer_near","water_deer_far","wild_boar_near","wild_boar_far")
      },
      "cross_study_night_zone_definition_harmonized":False,
      "between_study_difference_significance_claimed":False,
      "independent_study_event_record_overlap_excluded":False,
      "landscape_causal_effect_estimated":False,
      "original_2022_41_mirror_pairs_evaluated":False,
      "recommendation":"Obtain common night/twilight definitions, timestamp events, station on-time and season-matched comparison; test species×context interaction within physical cameras before causal interpretation."
    }

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--offline-han-html",type=Path)
    parser.add_argument("--offline-bukhansan-html",type=Path)
    args=parser.parse_args()
    try:
        plan=json.loads(PLAN.read_text())
        uplan=json.loads(ULJIN_PLAN.read_text())
        uljin=read_uljin(uplan,get_uljin_supp3())
        han=args.offline_han_html.read_text() if args.offline_han_html else official_kci_get(plan["sources"]["suburban_2024"]["url"])
        jeong=args.offline_bukhansan_html.read_text() if args.offline_bukhansan_html else official_kci_get(plan["sources"]["bukhansan_2025"]["url"])
        result=compare(plan,uljin,han,jeong)
    except (ValueError, KeyError, OSError, URLError, HTTPError, TimeoutError, TypeError) as e:
        result={"status":"HOLD_CROSS_STUDY_PUBLIC_SOURCE_VERIFICATION",
                "error_class":type(e).__name__,
                "cross_study_biological_claim_computed":False}
    print(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False))

if __name__=="__main__":
    main()
