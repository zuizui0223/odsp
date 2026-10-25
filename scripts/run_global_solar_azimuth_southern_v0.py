"""Four *pre-registered* Southern original Movebank GPS archives: azimuth v0.

All source taxonomy and origin decisions are fixed in two 2026-10-19 archived
source manifests; the solar-azimuth follow-on is frozen BEFORE its first
Southern azimuth outcomes. Previous other-response studies have been exposed;
this is exploratory, never untouched confirmation.
No exact animal coordinates/IDs/timestamps are exported.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
from pathlib import Path

from scripts.solar_azimuth_macro_v0 import analyze_taxon
from scripts.movebank_native_ecology_20261019 import (
    CATALOG,HERE,original_files,checksum_and_download
)
from scripts.movebank_solar_movement_20261019 import load_events
from scripts.movebank_southern_solar_mammal_20261019 import safe_unzip_data_csv
from scripts.movebank_utah_four_taxa_solar_20261019 import choose_from_timestamp

CONTRACT = HERE / "research/GLOBAL_SOLAR_AZIMUTH_SOUTHERN_SOURCE_V0_CONTRACT.json"
SOUTH = HERE / "research/MOVEBANK_SOUTHERN_SOLAR_MOVEMENT_V0_20261019.json"
KRUGER = HERE / "research/MOVEBANK_KRUGER_ELEPHANT_INDEPENDENT_V0_20261019.json"


def fixed_source_roster():
    spec=json.loads(CONTRACT.read_text(encoding="utf-8"))
    if spec["version"]!="global-solar-azimuth-southern-registered-sources-v0":
        raise ValueError("Southern solar azimuth protocol missing")
    southern=json.loads(SOUTH.read_text(encoding="utf-8"))
    kruger=json.loads(KRUGER.read_text(encoding="utf-8"))
    if southern["version"]!="southern-solar-matched-mammal-gps-v0" or len(southern["sources"])!=3:
        raise ValueError("Unexpected Southern original source frame")
    if kruger["version"]!="african-elephant-independent-kruger-source-v0":
        raise ValueError("Unexpected Kruger original source")
    first=[{
        "label":s["label"],"taxon":s["taxon"],"doi":s["doi"],"area":s["area"],
        "package_uuid":s["package_uuid"],"bitstream_uuid":s["provider_original_bitstream_uuid"],
        "md5":s["provider_original_md5"],"bytes":s["provider_original_bytes"],
        "zipped":s["provider_filename"].lower().endswith(".zip"),
        "license":s.get("rights","")
    } for s in southern["sources"]]
    s=kruger["source"]
    first.append({
        "label":s["label"],"taxon":s["taxon"],"doi":s["doi"],"area":"Kruger, South Africa",
        "package_uuid":s["package_uuid"],"bitstream_uuid":s["original_bitstream_uuid"],
        "md5":s["original_md5"],"bytes":s["original_bytes"],"zipped":False,
        "license":s.get("license","")
    })
    assert len(first)==4 and len({x["package_uuid"] for x in first})==4
    return first


def closest_to_hour(records):
    """Pre-response UTC timestamp-only selection, not a spatial trajectory filter."""
    chosen={}
    for timestamp,lat,lon in records:
        key=timestamp.replace(minute=0,second=0,microsecond=0)
        chosen[key]=choose_from_timestamp(chosen.get(key),(timestamp,lat,lon))
    return sorted(chosen.values())


def one_source(source,out_dir):
    result={
        "source":source["label"],"taxon":source["taxon"],
        "original_doi":source["doi"],"source_region":source["area"],
        "original_source_license_metadata":source["license"],
        "status":"SOURCE_HOLD"
    }
    orig=out_dir/("private_original.zip" if source["zipped"] else "private_original.csv")
    extracted=out_dir/"private_extracted.csv"
    try:
        files=original_files(source["package_uuid"])
        same=[x for x in files if x["bitstream_uuid"]==source["bitstream_uuid"]]
        if len(same)!=1 or same[0]["checksum"]["value"].lower()!=source["md5"].lower():
            raise ValueError("Original provider UUID/MD5 changed")
        if same[0]["bytes"]!=source["bytes"]:
            raise ValueError("Original provider bytes changed")
        result["provider_MD5_verification"]=checksum_and_download(same[0],orig)
        if source["zipped"]:
            safe_unzip_data_csv(orig,extracted)
            raw=extracted
        else:
            raw=orig
        tracks,nrows,bad=load_events(raw)
        result["original_rows"]=nrows
        result["invalid_source_rows"]=bad
        groups={animal:closest_to_hour(records) for animal,records in tracks.items()}
        result["valid_unique_UTC_hour_source_fixes"]=sum(len(x) for x in groups.values())
        result.update(analyze_taxon(groups))
        result["status"]="source_MD5_verified_original_GPS_azimuth_analyzed"
    except Exception as exc:
        result["status"]="SOURCE_HOLD"
        result["error"]=f"{type(exc).__name__}: {exc}"
    finally:
        orig.unlink(missing_ok=True)
        extracted.unlink(missing_ok=True)
    return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    all_packages=json.loads(CATALOG.read_text(encoding="utf-8"))["packages"]
    if len(all_packages)!=437:
        raise ValueError("Complete 437-package archive was modified")
    catalog={p["package_uuid"]:p for p in all_packages}
    sources=fixed_source_roster()
    for s in sources:
        if s["package_uuid"] not in catalog or s["taxon"] not in catalog[s["package_uuid"]]["scientific_names"]:
            raise ValueError("Source metadata no longer matches original 437-package snapshot")
    results=[]
    for source in sources:
        result=one_source(source,args.out)
        print("SOUTHERN_SOLAR_AZIMUTH_SOURCE "+json.dumps(result,sort_keys=True),flush=True)
        results.append(result)
    response={
        "version":"global-solar-azimuth-southern-registered-sources-v0",
        "n_pregistered_original_sources":len(sources),
        "n_verified_source_results":sum(x.get("status")=="source_MD5_verified_original_GPS_azimuth_analyzed" for x in results),
        "n_unavailable":sum(x["status"]=="SOURCE_HOLD" for x in results),
        "note":"One individual may appear in multiple source versions; Etosha animal taxa share one landscape. Animal-cluster intervals are descriptive, not biome-general. No observation-independent solar response.",
        "all_source_results":results
    }
    (args.out/"four_southern_original_source_group_results.json").write_text(
        json.dumps(response,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("SOUTHERN_SOLAR_AZIMUTH_SUMMARY "+json.dumps({
        "registered":len(sources),"verified":response["n_verified_source_results"],
        "unavailable":response["n_unavailable"]
    },sort_keys=True),flush=True)

if __name__=="__main__":
    main()
