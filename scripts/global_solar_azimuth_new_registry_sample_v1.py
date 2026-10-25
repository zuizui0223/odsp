"""Pre-outcome stratified sample of original Movebank GPS source DATA PACKAGES.

Does not read GPS event rows. Never selects replacements after an original
file/schema/UTC/cadence failure. All original provider calls metadata-only.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from scripts.movebank_native_ecology_20261019 import HERE, original_files

CONTRACT = HERE / "research/GLOBAL_SOLAR_AZIMUTH_INDEPENDENT_12SOURCE_V1_CONTRACT.json"
CATALOG = HERE / "research/seasonal_database_catalog/2026-10-19/movebank/catalog.json"
SEED = "odsp-azimuth-public-20261025-v1:"
FILE_SUFFIXES = (".csv", ".zip", ".csv.gz")


def metadata_stratum(p):
    names = set(str(x).strip() for x in p.get("scientific_names") or [] if str(x).strip())
    size = "large" if (p.get("reported_animal_count") or 0) >= 30 else "small"
    return ("multiple" if len(names) > 1 else "single") + "_" + size


def rank_key(p):
    return hashlib.sha256((SEED + p["package_uuid"]).encode("utf-8")).hexdigest()


def choose_all_strata(packages, contract):
    if len(packages) != 437 or len({x["package_uuid"] for x in packages}) != 437:
        raise ValueError("Complete archived 437-package snapshot changed")
    excluded = set(contract["previous_sources"])
    if len(excluded) != 9:
        raise ValueError("Previous nine source exclusion roster modified")
    original = {x["package_uuid"]:x for x in packages}
    if not excluded <= original.keys():
        raise ValueError("Prior-source archives missing from catalog")
    admitted = [
        p for p in packages
        if p["package_uuid"] not in excluded
        and any(label in ("GPS", "GNSS") for label in p.get("sensor_names") or [])
        and (p.get("reported_animal_count") or 0) >= 5
        and (p.get("reported_location_count") or 0) >= 10000
        and any(str(x).strip() for x in p.get("scientific_names") or [])
    ]
    if len(admitted) != contract["expected_frame_eligible_packages"]:
        raise ValueError("Frozen metadata eligibility count changed")
    groups = {}
    for item in admitted:
        groups.setdefault(metadata_stratum(item), []).append(item)
    expected = {"single_large","single_small","multiple_large","multiple_small"}
    if set(groups) != expected or any(len(v) < 3 for v in groups.values()):
        raise ValueError("Four preregistered strata have insufficient metadata candidates")
    selection = []
    for group in sorted(groups):
        for original_rank, p in enumerate(sorted(groups[group],key=rank_key)[:3], start=1):
            selection.append((group, original_rank, p))
    if len(selection) != 12:
        raise ValueError("Not exactly three from each of four strata")
    # deterministic order for 3 source jobs with fixed modulo-3 assignment.
    return selection, {g:len(p) for g,p in sorted(groups.items())}


def one_metadata_package(group, rank, p):
    entry = {
        "package_uuid":p["package_uuid"],
        "original_dois":p.get("dois") or [],
        "source_study_ids":p.get("repository_study_ids") or [],
        "original_species_labels":sorted(set(p.get("scientific_names") or [])),
        "original_sensor_labels":p.get("sensor_names") or [],
        "original_licenses":p.get("licenses") or [],
        "reported_registry_animals":p.get("reported_animal_count"),
        "reported_registry_locations":p.get("reported_location_count"),
        "sample_stratum":group,
        "within_stratum_metadata_rank":rank,
        "preoutcome_hash_rank":rank_key(p),
        "status":"SOURCE_HOLD",
        "original_file":None,
        "animal_event_rows_opened":0,
    }
    try:
        original = original_files(p["package_uuid"])
        data = [x for x in original if str(x.get("name") or "").lower().endswith(FILE_SUFFIXES)
                and "reference-data" not in str(x.get("name") or "").lower()
                and "__macosx" not in str(x.get("name") or "").lower()
                and not str(x.get("name") or "").split("/")[-1].startswith("._")]
        entry["original_bundle_bitstreams"]=len(original)
        entry["candidate_source_data_containers"]=len(data)
        if len(data) != 1:
            entry["hold_reason"]="expected exactly one filename-qualified original data container"
            return entry
        f=data[0]
        entry["original_file"]={
            "bitstream_uuid":f["bitstream_uuid"],"filename":f["name"],
            "bytes":f["bytes"],"checksum":f["checksum"]}
        if not isinstance(f["bytes"],int) or not (64<=f["bytes"]<=120000000):
            entry["hold_reason"]="original file outside preregistered 64B to 120MB transfer cap"
            return entry
        ck=f.get("checksum") or {}
        if ck.get("checkSumAlgorithm","").upper() not in ("MD5","SHA256","SHA-256") or not ck.get("value"):
            entry["hold_reason"]="no supported provider checksum"
            return entry
        entry["status"]="ORIGINAL_FILE_METADATA_ADMISSIBLE"
    except Exception as e:
        entry["hold_reason"]=f"{type(e).__name__}: {e}"
    return entry


def build_source_frame(rows, contract):
    selected, strata_counts=choose_all_strata(rows,contract)
    result=[one_metadata_package(group,rank,p) for group,rank,p in selected]
    return {
        "version":contract["version"],
        "frozen_original_catalog_packages":437,
        "metadata_eligible_framed_packages":contract["expected_frame_eligible_packages"],
        "metadata_strata_eligible_counts":strata_counts,
        "selection_seed":SEED,
        "selected_packages":len(result),
        "file_metadata_admissible":sum(x["status"]=="ORIGINAL_FILE_METADATA_ADMISSIBLE" for x in result),
        "original_source_metadata_holds":sum(x["status"]=="SOURCE_HOLD" for x in result),
        "sample_original_file_source_entries":result,
        "interpretation":"No source original GPS positions, timestamps or movement outcomes opened; source FILE metadata only. No replacement of 12 original package UUIDs for technical failure."
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract["version"]!="global-azimuth-prospective-independent-source-frame-v1":
        raise ValueError("Selection contract/version changed")
    catalog=json.loads(CATALOG.read_text(encoding="utf-8"))
    result=build_source_frame(catalog["packages"],contract)
    target=args.out/"v1_frozen_sample_original_provider_file_metadata.json"
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("AZIMUTH_NEW_SOURCE_SAMPLE_METADATA "+
          json.dumps(result,ensure_ascii=False,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
