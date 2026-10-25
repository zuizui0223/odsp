"""Complete public Movebank GPS/GNSS original-bitstream METADATA census.

Uses exact frozen 437-package registry, ALL 259 GPS/GNSS-labeled sources,
returns no actual GPS rows. DOI & source study ID recorded for deduplication.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse,json
from pathlib import Path
from scripts.movebank_native_ecology_20261019 import CATALOG,original_files

SUFFIXES=(".csv",".zip",".csv.gz",".tsv",".txt",".parquet")

def row_for_package(p):
    out={
        "package_uuid":p["package_uuid"],
        "repository_study_ids":p.get("repository_study_ids") or [],
        "original_scientific_name_labels":p.get("scientific_names") or [],
        "original_sensor_name_labels":p.get("sensor_names") or [],
        "dois":p.get("dois") or [],
        "licenses":p.get("licenses") or [],
        "registry_reported_animal_count":p.get("reported_animal_count"),
        "registry_reported_location_count":p.get("reported_location_count"),
        "catalog_meta_only_priority":bool(
            (p.get("reported_animal_count") or 0)>=5
            and (p.get("reported_location_count") or 0)>=10000),
        "source_status":"SOURCE_HOLD",
        "source_original_bitstream_count":None,
        "candidate_original_track_containers":[],
        "animal_event_rows_screened":0
    }
    try:
        files=original_files(p["package_uuid"])
        out["source_original_bitstream_count"]=len(files)
        out["source_status"]="original_metadata_listed"
        out["candidate_original_track_containers"]=[
            {
                "bitstream_uuid":x["bitstream_uuid"],
                "file_name":x["name"],
                "size_bytes":x["bytes"],
                "provider_checksum":x.get("checksum"),
                "suffix_hint_only":True,
                "original_bytes_or_schema_verified":False
            }
            for x in files
            if str(x.get("name") or "").lower().endswith(SUFFIXES)
            and "reference-data" not in str(x.get("name") or "").lower()
        ]
    except Exception as ex:
        out["source_status"]="SOURCE_HOLD"
        out["source_error"]=f"{type(ex).__name__}: {ex}"
    return out


def summary(rows):
    n=len(rows)
    if n!=259 or len({x["package_uuid"] for x in rows})!=259:
        raise ValueError("Candidate original full 259 source frame lost or duplicated")
    study={}
    for r in rows:
        for sid in set(r["repository_study_ids"]):
            study[sid]=study.get(sid,0)+1
    counts={
        "candidate_public_original_GPS_or_GNSS_packages":n,
        "packages_with_original_metadata_resolved":sum(x["source_status"]=="original_metadata_listed" for x in rows),
        "source_HOLD_packages":sum(x["source_status"]=="SOURCE_HOLD" for x in rows),
        "packages_with_a_candidate_file_suffix":sum(bool(x["candidate_original_track_containers"]) for x in rows),
        "candidate_original_file_containers":sum(len(x["candidate_original_track_containers"]) for x in rows),
        "candidate_packages_with_md5_or_sha_metadata":sum(
            any(y.get("provider_checksum",{}).get("value") for y in x["candidate_original_track_containers"])
            for x in rows),
        "metadata_priority_packages":sum(x["catalog_meta_only_priority"] for x in rows),
        "distinct_repository_study_ids":len(study),
        "study_ids_repeated_on_more_than_one_package":sum(x>1 for x in study.values()),
        "packages_missing_repository_study_ids":sum(not x["repository_study_ids"] for x in rows),
        "time_and_position_schema_validated_packages":0,
        "geographic_independent_field_populations_certified":0,
        "notes":"File suffixes indicate possible original GPS containers only, not admissible GPS data, access permissions, or independent study populations."
    }
    return counts


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--workers",type=int,default=6)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    catalog=json.loads(CATALOG.read_text(encoding="utf-8"))
    if len(catalog["packages"])!=437:
        raise ValueError("Frozen complete registry frame changed")
    selected=[x for x in catalog["packages"]
              if any(s in ("GPS","GNSS") for s in (x.get("sensor_names") or []))]
    if len(selected)!=259:
        raise ValueError("Source-blind GPS/GNSS candidate frame does not match predeclared 259")
    data=[]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        fs=[pool.submit(row_for_package,p) for p in selected]
        for f in as_completed(fs):
            data.append(f.result())
    data.sort(key=lambda r:r["package_uuid"])
    counts=summary(data)
    (args.out/"all_259_original_source_file_metadata.json").write_text(
        json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (args.out/"all_259_metadata_screen_summary.json").write_text(
        json.dumps(counts,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("GLOBAL_SOLAR_259_SOURCE_PREFLIGHT "+json.dumps(counts,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
