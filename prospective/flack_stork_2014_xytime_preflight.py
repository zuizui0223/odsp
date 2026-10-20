#!/usr/bin/env python3
"""Outcome-blind 2014 Flack/Weinzierl white stork cohort comparison audit.

A different public Movebank study from the 2013 Rotics source. The biological
question is a *separate-cohort* replication at the already established 50km
migration grain. This reads timestamp, bird/tag ID, x/y, speed and age only.
No numeric height values or distributions can enter the admission decision.
"""
from __future__ import annotations

import argparse,csv,hashlib,io,json,zipfile
from pathlib import Path
from . import stork_2014_xytime_source_screen as core

ZIP_NAME="Fall migration of white storks in 2014-gps.csv.zip"
ZIP_MD5="c1fa0c4ca28d3fce5d61caaac36e87d2"
REF_NAME="Fall migration of white storks in 2014-reference-data.csv"
REF_MD5="116a3d82cd11e1bb4e16b32532725359"
SOURCE="10.5441/001/1.bj96m274"


def check(path:Path,expected_name:str,expected_md5:str):
    digest=hashlib.md5()
    with path.open("rb") as stream:
        for buf in iter(lambda:stream.read(1048576),b""):
            digest.update(buf)
    if path.name!=expected_name or digest.hexdigest()!=expected_md5:
        raise ValueError("Independent 2014 archived file checksum/name mismatch")
    return digest.hexdigest()


def get_source_csv_names(zf:zipfile.ZipFile):
    names=[x for x in zf.namelist()
           if x.lower().endswith(".csv") and not x.startswith("__MACOSX")
           and not x.rsplit("/",1)[-1].startswith("._")]
    if len(names)!=1:
        raise ValueError("Expected one non-resourcefork native GPS CSV, found "+str(names))
    return names[0]


def outcome_blind_audit(zip_path:Path,reference:Path):
    check(zip_path,ZIP_NAME,ZIP_MD5)
    check(reference,REF_NAME,REF_MD5)
    with reference.open("rt",encoding="utf-8-sig",newline="") as fp:
        ages, refmeta=core.read_reference(csv.DictReader(fp))
    if core.YEAR!=2014 or core.GRIDS_M!=(5000,50000,100000):
        raise ValueError("Older freeze changed; do not continue")
    with zipfile.ZipFile(zip_path) as zf:
        name=get_source_csv_names(zf)
        with zf.open(name) as blob,io.TextIOWrapper(blob,encoding="utf-8-sig",newline="") as reader:
            rows=csv.DictReader(reader)
            cols=set(rows.fieldnames or [])
            needed={"timestamp","individual-local-identifier","location-long","location-lat","ground-speed"}
            if not needed<=cols:
                raise ValueError("Native GPS lacks pre-registered nonvertical columns: "+str(needed-cols))
            outcome=core.audit(rows,ages)
            have_height="height-above-ellipsoid" in cols
            have_horizontal_accuracy="eobs:horizontal-accuracy-estimate" in cols or "e-obs:horizontal-accuracy-estimate" in cols

    output={
        "analysis":"FLACK_WHITE_STORK_2014_DISTINCT_COHORT_XYTIME_GATE_V1",
        "source":"https://doi.org/10.5441/001/1.bj96m274",
        "source_movebank_study":332044860,
        "source_zip_md5":ZIP_MD5,
        "source_reference_md5":REF_MD5,
        "source_gps_member":name,
        "source_file_age":refmeta,
        "native_ellipsoid_height_column_exists":have_height,
        "native_horizontal_accuracy_column_exists":have_horizontal_accuracy,
        "year_2014_biological_height_opened":False,
        "age_or_time_metadata_only":True,
        "reference_A": "Year and movement filtering identical to 2013 stork code; this is independent source and never claims direct 5km transport.",
        "old_2013_evidence_recomputed":False,
        "frozen_primary_50km":outcome["horizontal_support_by_grid_m"]["50000"],
        "descriptive_5km":outcome["horizontal_support_by_grid_m"]["5000"],
        "descriptive_100km":outcome["horizontal_support_by_grid_m"]["100000"],
        "source_event_metadata":outcome["GPS_time_speed_xy_rows"],
        "age_metadata_event_counts":outcome["thinned_fixes_by_reference_age_label"],
        "source_native_taxon_assumed":"Ciconia ciconia as archived species; inspect reference label before inferential claims",
    }
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gps-zip",required=True,type=Path)
    parser.add_argument("--reference",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    outcome=outcome_blind_audit(args.gps_zip,args.reference)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(outcome,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "source_unique_animals":outcome["source_file_age"]["unique_birds"],
        "year_2014_gps_birds":outcome["source_event_metadata"]["birds_with_thinned_flight"],
        "5km_birds":outcome["descriptive_5km"]["birds_with_2_scorable_shared_cell_days"],
        "50km_birds":outcome["frozen_primary_50km"]["birds_with_2_scorable_shared_cell_days"],
        "50km_admitted":outcome["frozen_primary_50km"]["admitted"],
        "100km_birds":outcome["descriptive_100km"]["birds_with_2_scorable_shared_cell_days"],
        "altitude_opened":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
