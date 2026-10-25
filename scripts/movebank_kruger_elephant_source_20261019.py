"""Original Kruger elephant source as an independent intraspecific ecology comparison.

Original provider-MD5 data and complete frozen 437-package cohort remain unchanged.
Primary equals the previously fixed Etosha hourly-v1 observation rule; all
movement estimates, nulls and insufficient outcomes are printed source-aggregated.
"""
import argparse,csv,json
from pathlib import Path
from scripts.movebank_native_ecology_20261019 import HERE,original_files,checksum_and_download
from scripts.movebank_elephant_hourly_20261019 import thinned_loader
from scripts.movebank_solar_movement_20261019 import load_events as native_loader
from scripts import movebank_southern_solar_mammal_20261019 as south

CONTRACT=HERE/"research/MOVEBANK_KRUGER_ELEPHANT_INDEPENDENT_V0_20261019.json"
CATALOG=HERE/"research/seasonal_database_catalog/2026-10-19/movebank/catalog.json"

def read_column_names_only(path):
    with path.open(encoding="utf-8-sig",newline="") as src:
        rd=csv.reader(src)
        return next(rd,[])

def source_estimand(path,loader):
    previous=south.load_events
    try:
        south.load_events=loader
        return south.analyze_south(path)
    finally:
        south.load_events=previous

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    fixed=json.loads(CONTRACT.read_text())
    assert fixed["version"]=="african-elephant-independent-kruger-source-v0"
    source=fixed["source"]
    packages=json.loads(CATALOG.read_text(encoding="utf-8"))["packages"]
    assert len(packages)==437
    matched=[p for p in packages if p["package_uuid"]==source["package_uuid"]]
    if len(matched)!=1 or "Loxodonta africana" not in matched[0]["scientific_names"]:
        raise ValueError("Original preselected metadata population/taxon mismatch")
    result={"source":source["label"],"taxon":source["taxon"],"doi":source["doi"],
            "original_dataset_license":source["license"],
            "comparator_etosha_hourly_reference":-0.15012724713090492,
            "observation_protocol":"Identical to source-locked Etosha elephant time-only hourly v1"}
    dest=args.out/"kruger_source.csv"
    try:
        files=original_files(source["package_uuid"])
        streams=[f for f in files if f["bitstream_uuid"]==source["original_bitstream_uuid"]]
        if len(streams)!=1 or streams[0]["checksum"]["value"].lower()!=source["original_md5"].lower() or streams[0]["bytes"]!=source["original_bytes"]:
            raise ValueError("Provider original CSV identity/MD5/size mismatch")
        result["provider_original_integrity"]=checksum_and_download(streams[0],dest)
        result["original_csv_columns"]=read_column_names_only(dest)
        result["hourly_v1"]=source_estimand(dest,thinned_loader)
        result["hourly_v1_sampling_summary"]=thinned_loader.counts
        result["original_native_adjacent_v0"]=source_estimand(dest,native_loader)
        result["status"]="source_estimator_completed"
    except Exception as e:
        result.update(status="source_hold",reason=f"{type(e).__name__}: {e}")
    finally:
        dest.unlink(missing_ok=True)
    print("KRUGER_ELEPHANT_SOURCE_ECOLOGY "+json.dumps(result,sort_keys=True),flush=True)
    (args.out/"kruger_elephant_grouped.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
if __name__=="__main__":main()
