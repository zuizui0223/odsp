#!/usr/bin/env python3
"""Source independence ledger: published Scacco 2026 parent vs France 2019-21.

Read ONLY native source segment metadata from official Scacco data archive and
the previously frozen French bird-ID/XYtime source receipt. NO native GPS or
barometric height fields are opened in either source.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,zipfile
from collections import Counter,defaultdict
from pathlib import Path

SCACCO_ZIP="Data.zip"
SCACCO_BYTES=551470630
SCACCO_MD5="e1f116e6576cf20e54dad16d2c91a26d"
META_FILE="BIOLOGGING_finalSummaryDataset_perSegment_fromFix+COTvariables_Feb2025.csv"
PREV_IDS={"122120597","44080734"}
SPECIES="Gyps fulvus"
FRENCH_SOURCE="Eurasian griffon vulture in France (Grands Causses 2018) ID_PROG 961"
FRENCH_HASH="031d6226418cc0291a48d7d4eb44f1cae003df3a411ef3767a5229dbd45b1928"


def normalize_name(value):
    return " ".join((value or "").casefold().split())


def hash_ids(ids):
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


def source_segments(reader,france):
    if not {"studyID","studyName","species","individualID","segmentID","dataSource"} <= set(reader.fieldnames or []):
        raise ValueError("Original 2026 study/animal source columns not present")
    old={id:{"names":Counter(),"birds":set(),"source":Counter(),
             "segments":0,"segment_days":set()}
         for id in PREV_IDS}
    for row in reader:
        source=(row.get("studyID") or "").strip()
        if source not in old or (row.get("species") or "").strip()!=SPECIES:
            continue
        rec=old[source]
        name=(row.get("studyName") or "").strip()
        bird=(row.get("individualID") or "").strip()
        if name:rec["names"][name]+=1
        if bird:rec["birds"].add(bird)
        source_code=(row.get("dataSource") or "").strip()
        if source_code:rec["source"][source_code]+=1
        day=(row.get("segm_timeStart") or "")[:10]
        if len(day)==10:rec["segment_days"].add(day)
        rec["segments"]+=1
    original=set(france["selected_animal_IDs"])
    neweligible=set(france["horizontal_day_eligibility_by_cell_m"]["5000"]["admitted_bird_ids"])
    if (len(original),len(neweligible))!=(30,28):
        raise ValueError("Original altitude-blind French source bird roster changed")
    if hash_ids(neweligible)!=FRENCH_HASH:
        raise ValueError("French 5km candidate bird ID SHA differs from preserved eligibility")
    panels={}
    name_found_match=False
    all_id_overlap=set()
    for id,entry in sorted(old.items()):
        if not entry["birds"] or not entry["names"]:
            raise ValueError(f"Scacco original study {id} absent from archive metadata")
        match=any(normalize_name(name)==normalize_name(FRENCH_SOURCE)
                  for name in entry["names"])
        name_found_match |=match
        animal_overlap=entry["birds"]&original
        all_id_overlap |=animal_overlap
        panels[id]={
            "species":SPECIES,
            "source_study_names":dict(entry["names"]),
            "unique_original_source_birds":len(entry["birds"]),
            "source_bird_id_sha256":hash_ids(entry["birds"]),
            "source_segments":entry["segments"],
            "native_tracking_days":len(entry["segment_days"]),
            "original_dataSource_labels":dict(entry["source"]),
            "exact_study_name_matches_French":match,
            "exact_bird_ID_overlap_all_French_30":len(animal_overlap),
            "exact_bird_ID_overlap_eligible_French_28":len(entry["birds"]&neweligible)
        }
    if all_id_overlap or name_found_match:
        classification="SOURCE_OR_ANIMAL_OVERLAP_REQUIRES_REVIEW"
    else:
        classification="DIFFERENT_STUDY_NAMES_AND_ZERO_EXACT_SOURCE_ANIMAL_IDS"
    return {
        "analysis":"SCACCO_VS_FRANCE_WILD_GYPS_SOURCE_METADATA_NONOVERLAP_V1",
        "stage":"PREHEIGHT_CROSS_ARCHIVE_MOVE_BANK_PARENT_LABEL_CHECK",
        "Scacco_source_DOI":"10.5281/zenodo.21915776",
        "Scacco_source_md5":SCACCO_MD5,
        "French_source_DOI":"10.48579/PRO/IOSZNM",
        "French_source_name":FRENCH_SOURCE,
        "French_original_source_run":39714803696,
        "French_source_five_minute_birds_all":len(original),
        "French_5km_bird_fingerprint":FRENCH_HASH,
        "original_2026_Gyps_study_comparison":panels,
        "source_independence_category":classification,
        "exact_bird_id_overlap_across_both_2026_Gyps_parents":len(all_id_overlap),
        "exact_parent_study_numeric_id_for_French_obtained":False,
        "tag_serial_crosswalk_complete":False,
        "native_height_values_read":False,
        "altitude_missingness_checked":False,
        "ecological_effect_tested":False,
        "claim_limit":"Different labels/animal ID strings establish absence of literal overlap in these archived sources, NOT definitively different biological animals or devices, or independence of underlying research group/environment."
    }


def checked_zip(path):
    if path.name!=SCACCO_ZIP or path.stat().st_size!=SCACCO_BYTES:
        raise ValueError("Archived 2026 source filename/bytes changed")
    h=hashlib.md5()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    if h.hexdigest()!=SCACCO_MD5:
        raise ValueError("Archived 2026 source MD5 changed")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-2026",type=Path,required=True)
    p.add_argument("--france-source",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    checked_zip(args.source_2026)
    france=json.loads(args.france_source.read_text())
    if france["numeric_native_GPS_height_values_read"] is not False:
        raise ValueError("France XY-only source receipt no longer altitude-blind")
    with zipfile.ZipFile(args.source_2026) as z:
        names=[i for i in z.namelist()
               if i.endswith("/"+META_FILE) or i==META_FILE]
        if len(names)!=1:
            raise ValueError("Expected one original per-flight-segment source metadata table")
        with z.open(names[0]) as f:
            text=io.TextIOWrapper(f,encoding="utf-8-sig",newline="")
            result=source_segments(csv.DictReader(text),france)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "classification":result["source_independence_category"],
        "exact_bird_ID_overlap":result["exact_bird_id_overlap_across_both_2026_Gyps_parents"],
        "source_parent_study_names":{
             id:list(x["source_study_names"]) for id,x in result["original_2026_Gyps_study_comparison"].items()
        },
        "native_height_opened":False
    },sort_keys=True))

if __name__=="__main__":
    main()
