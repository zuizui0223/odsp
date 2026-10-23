#!/usr/bin/env python3
"""Crosswalk French original 2019–2021 Gyps with Scacco source parents.

Reads ONLY Scacco 2026 per-SEGMENT study/species/bird identifiers, names,
source recording years and optional tag fields; and the ORIGINAL altitude-blind
French bird roster receipt. Never opens native GPS altitudes in either archive.

The literal geodesy-test label is not a biological bird, and was never a
member of the previously frozen 5km 28-bird population. Flag and remove it
from descriptive 50km counts before source independence conclusions.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,unicodedata,zipfile
from collections import Counter,defaultdict
from pathlib import Path

SOURCE_ZIP="Data.zip"
SOURCE_MD5="e1f116e6576cf20e54dad16d2c91a26d"
SOURCE_BYTES=551470630
SEGMENT="BIOLOGGING_finalSummaryDataset_perSegment_fromFix+COTvariables_Feb2025.csv"
OLD_STUDIES=("122120597","44080734")
FRANCE_STUDY="Eurasian griffon vulture in France (Grands Causses 2018) ID_PROG 961"
EXCLUDED_CALIBRATION="Test géodésie ornitela"
FRANCE_5KM_HASH="031d6226418cc0291a48d7d4eb44f1cae003df3a411ef3767a5229dbd45b1928"
OLD_STUDY_SPECIES="Gyps fulvus"


def norm(s):
    s=unicodedata.normalize("NFKC",str(s or "")).casefold()
    return " ".join(s.split())


def check_zip(path):
    if path.name!=SOURCE_ZIP or path.stat().st_size!=SOURCE_BYTES:
        raise ValueError("Scacco source archive name or byte size mismatch")
    h=hashlib.md5()
    with path.open("rb") as fp:
        for block in iter(lambda:fp.read(1048576),b""):
            h.update(block)
    if h.hexdigest()!=SOURCE_MD5:
        raise ValueError("Scacco original source checksum mismatch")
    return h.hexdigest()


def source_studies(reader):
    required={"studyName","studyID","individualID","species","dataSource"}
    if not required.issubset(set(reader.fieldnames or ())):
        raise ValueError("Missing Scacco original segment study identity columns")
    sources=defaultdict(lambda: {
        "birds":set(),"study_names":Counter(),"n_segments":0,
        "years":Counter(),"data_sources":Counter(),
        "optional_tags":set()
    })
    all_non_gyps=0
    for r in reader:
        if (r.get("species") or "").strip()!=OLD_STUDY_SPECIES:
            all_non_gyps+=1
            continue
        study=(r.get("studyID") or "").strip()
        bird=(r.get("individualID") or "").strip()
        study_name=(r.get("studyName") or "").strip()
        if not bird:continue
        key=study or "NO_NUMERIC_STUDY"
        x=sources[key]
        x["n_segments"]+=1
        x["birds"].add(bird)
        x["study_names"][study_name]+=1
        x["data_sources"][(r.get("dataSource") or "").strip()]+=1
        stamp=(r.get("segm_timeStart") or "").strip()
        if len(stamp)>=4 and stamp[:4].isdigit():
            x["years"][stamp[:4]]+=1
        for candidate in ("tagID","tag.id","tagLocalIdentifier","tag-local-identifier"):
            val=(r.get(candidate) or "").strip()
            if val:x["optional_tags"].add(val)
    return sources,all_non_gyps


def crosswalk(source, french):
    if french.get("phase")!="FRENCH_GYPS_2019_2021_XYTIME_INSTRUMENT_ONLY_PREHEIGHT":
        raise ValueError("French receipt not from original no-height source gate")
    if french.get("numeric_native_GPS_height_values_read") is not False:
        raise ValueError("Cannot call a previously height-screened French source independent")
    if french.get("source_zip_md5")!="b18cc8004d311d19ff24060f655178bf":
        raise ValueError("France source MD5 drift")
    g=french.get("horizontal_day_eligibility_by_cell_m") or {}
    orig5=g["5000"]
    orig50=g["50000"]
    f5=set(orig5["admitted_bird_ids"])
    f50=set(orig50["admitted_bird_ids"])
    if (len(f5)!=28 or orig5["source_bird_ID_sha256"]!=FRANCE_5KM_HASH
       or EXCLUDED_CALIBRATION in f5):
        raise ValueError("Original French 5km source roster changed or contains explicit test device")
    if len(f50)!=29 or EXCLUDED_CALIBRATION not in f50:
        raise ValueError("50km source nonanimal test-device metadata no longer as audited")
    canonical50=f50-{EXCLUDED_CALIBRATION}
    if len(canonical50)!=28:
        raise ValueError("Unexpected 50km biological source sample after geodesy control")
    listed=set(french["selected_animal_IDs"])
    if EXCLUDED_CALIBRATION not in listed or len(listed)!=30:
        raise ValueError("Full French source ID universe changed")
    if not f5<=listed or not canonical50<=listed:
        raise ValueError("French 5km/50km frozen source IDs not in original source cohort")

    french_id_values={norm(v) for v in listed if v!=EXCLUDED_CALIBRATION}
    french_five_values={norm(v) for v in f5}
    french_name_norm=norm(FRANCE_STUDY)
    direct_named_parents=[]
    all_studies=[]
    for study,x in sorted(source.items()):
        study_names=sorted(x["study_names"])
        overlap=set(x["birds"])&(listed-{EXCLUDED_CALIBRATION})
        five_overlap=set(x["birds"])&f5
        names_match=[name for name in study_names if norm(name)==french_name_norm]
        names_related=[
            name for name in study_names if
            "causses" in norm(name) or
            ("prog 961" in norm(name) and "griffon" in norm(name))
        ]
        normalized_overlap=[
            bird for bird in x["birds"] if norm(bird) in french_id_values
        ]
        if names_match:
            direct_named_parents.append(study)
        all_studies.append({
            "source_study_ID":study,
            "reported_study_names":study_names,
            "source_bird_count":len(x["birds"]),
            "n_source_flight_segments":x["n_segments"],
            "source_years":dict(sorted(x["years"].items())),
            "source_data_providers":dict(sorted(x["data_sources"].items())),
            "same_study_name_exact_as_France":bool(names_match),
            "possibly_related_causses_programme961_name":bool(names_related),
            "n_exact_animal_id_overlap_all30_excluding_test":len(overlap),
            "n_exact_animal_id_overlap_5km28":len(five_overlap),
            "n_casefold_normalized_animal_id_overlap":len(normalized_overlap),
            "source_tag_values_exported_count":len(x["optional_tags"]),
            "tag_crosswalk_verified":False,
        })

    old_subset=[z for z in all_studies if z["source_study_ID"] in OLD_STUDIES]
    if len(old_subset)!=2:
        raise ValueError("Both original Gyps fulvus studies must be present in source CSV")
    exact_bird_overlap=sum(z["n_exact_animal_id_overlap_5km28"] for z in all_studies)
    name_or_source_overlap=bool(direct_named_parents or exact_bird_overlap)
    state=(
        "POTENTIAL_SAME_STUDY_PARENT_OR_BIRDS"
        if name_or_source_overlap else
        "NO_LITERAL_STUDY_NAME_OR_BIRD_ID_OVERLAP_PARENT_ID_UNCONFIRMED"
    )
    return {
      "analysis":"FRANCE_VS_SCACCO_GYPS_PARENT_BIRD_LITERAL_JOIN_V1",
      "stage":"SOURCE_METADATA_CROSSWALK_BEFORE_FRANCE_HEIGHT_OPENING",
      "France_source_Dataverse_DOI":"10.48579/PRO/IOSZNM",
      "France_source_study_name":FRANCE_STUDY,
      "Scacco_source_Zenodo_DOI":"10.5281/zenodo.21915776",
      "Scacco_source_zip_md5":SOURCE_MD5,
      "Scacco_source_older_positive_Gyps_study_IDs":list(OLD_STUDIES),
      "France_original_source_reported_animal_labels":len(listed),
      "France_calibration_or_test_label":EXCLUDED_CALIBRATION,
      "France_biological_source_animal_labels_after_explicit_test_exclusion":len(listed)-1,
      "France_original_5km_biological_birds":len(f5),
      "France_5km_bird_ids_sha256":FRANCE_5KM_HASH,
      "France_original_50km_bird_labels":len(f50),
      "France_corrected_50km_biological_birds":len(canonical50),
      "France_corrected_50km_bird_ids_sha256":hashlib.sha256("\n".join(sorted(canonical50)).encode()).hexdigest(),
      "France_biological_5km_sample_unchanged":True,
      "previous_Gyps_fulvus_source_study_counts":len(all_studies),
      "original_positive_Gyps_source_studies":old_subset,
      "all_Gyps_fulvus_source_studies":all_studies,
      "exact_study_name_matches":direct_named_parents,
      "exact_bird_ID_overlap_with_any_old_Gyps_study":exact_bird_overlap,
      "independence_class":state,
      "fully_independent_device_or_parent_confirmed":False,
      "native_GPS_altitude_value_read":False,
      "native_altitude_missingness_checked":False,
      "original_altitude_results_reused_or_recomputed":False,
      "no_overclaim":"Different study names and no exact bird IDs are helpful but do not prove distinct parent Movebank study or different physical GPS tags. Same source content, overlapping subjects, different data exports can remain possible."
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scacco-zip",type=Path,required=True)
    p.add_argument("--french-xy-receipt",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    arg=p.parse_args()
    check_zip(arg.scacco_zip)
    french=json.loads(arg.french_xy_receipt.read_text(encoding="utf-8"))
    with zipfile.ZipFile(arg.scacco_zip) as zf:
        member=[v for v in zf.namelist()
                if v.endswith("/"+SEGMENT)
                or v==SEGMENT]
        if len(member)!=1:raise ValueError("Original segment CSV archive path drift")
        with zf.open(member[0]) as binary:
            with io.TextIOWrapper(binary,encoding="utf-8-sig",newline="") as fp:
                original,non_gyp=source_studies(csv.DictReader(fp))
    outcome=crosswalk(original,french)
    outcome["original_non_Gyps_fulvus_segment_rows_read_headers_only"]=non_gyp
    arg.out.parent.mkdir(parents=True,exist_ok=True)
    arg.out.write_text(json.dumps(outcome,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps({
      "status":outcome["independence_class"],
      "source_studies_all_Gyps_fulvus":outcome["previous_Gyps_fulvus_source_study_counts"],
      "old_positive_studies":{p["source_study_ID"]:p["reported_study_names"]
                              for p in outcome["original_positive_Gyps_source_studies"]},
      "exact_France_study_name_matches":outcome["exact_study_name_matches"],
      "same_bird_IDs":outcome["exact_bird_ID_overlap_with_any_old_Gyps_study"],
      "France_5km_biological_birds":outcome["France_original_5km_biological_birds"],
      "France_50km_birds_after_test_exclusion":outcome["France_corrected_50km_biological_birds"],
      "altitude_opened":False
    },sort_keys=True))


if __name__=="__main__":
    main()
