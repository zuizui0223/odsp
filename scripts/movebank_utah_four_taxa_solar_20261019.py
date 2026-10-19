"""One public Utah ungulate study, four species, time-only hourly solar displacement.

Source-locked AFTER public registry enumeration, BEFORE Utah outcome access.
Report only taxon-source-level aggregates, not animal positions, timestamps or IDs.
"""
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import argparse,csv,io,json,math
from zipfile import ZipFile
from scripts.movebank_native_ecology_20261019 import HERE,original_files,checksum_and_download,parse_time
from scripts import movebank_solar_movement_20261019 as north

CONTRACT=HERE/"research/MOVEBANK_UTAH_FOUR_TAXA_SOLAR_V0_20261019.json"
CATALOG=HERE/"research/seasonal_database_catalog/2026-10-19/movebank/catalog.json"

def choose_from_timestamp(previous,current):
    """Keep record closest to UTC hour start. previous/current=(t,lat,lon)."""
    if previous is None:return current
    def offset(row):
        t=row[0]
        return (t-t.replace(minute=0,second=0,microsecond=0)).total_seconds()
    return current if offset(current)<offset(previous) else previous

def extract_time_only_original_source(original_zip, frozen_taxa):
    """Stream large ZIP once; never uncompress 840MB disk or publish raw tracks."""
    groups={t:defaultdict(dict) for t in frozen_taxa}
    source_counts={t:{"rows":0,"valid_rows":0,"invalid_rows":0} for t in frozen_taxa}
    other_taxa=0
    with ZipFile(original_zip) as archive:
        members=[m for m in archive.infolist()
                 if not m.is_dir() and m.filename.lower().endswith(".csv")
                 and not m.filename.startswith("__MACOSX/")
                 and not m.filename.rsplit("/",1)[-1].startswith("._")
                 and "reference-data" not in m.filename.lower()]
        if len(members)!=1:raise ValueError("Expected exactly one provider original tracking CSV")
        m=members[0]
        if m.file_size>1_200_000_000:raise ValueError("Unexpected larger-than-frozen original tracking archive")
        with archive.open(m) as binary,io.TextIOWrapper(binary,encoding="utf-8-sig",newline="") as text_file:
            rdr=csv.DictReader(text_file)
            columns={k.strip().lower():k for k in (rdr.fieldnames or [])}
            required=["timestamp","location-lat","location-long","individual-local-identifier","individual-taxon-canonical-name"]
            if not all(k in columns for k in required):raise ValueError("Native Utah source required columns absent")
            for record in rdr:
                taxon=(record[columns["individual-taxon-canonical-name"]] or "").strip()
                if taxon not in groups:
                    other_taxa+=1
                    continue
                stat=source_counts[taxon]
                stat["rows"]+=1
                timestamp=parse_time(record.get(columns["timestamp"],""))
                animal=(record.get(columns["individual-local-identifier"]) or "").strip()
                try:
                    lat=float(record[columns["location-lat"]])
                    lon=float(record[columns["location-long"]])
                except (TypeError,ValueError,KeyError):
                    lat=lon=float("nan")
                if not animal or timestamp is None or not (math.isfinite(lat) and math.isfinite(lon) and abs(lat)<=90 and abs(lon)<=180):
                    stat["invalid_rows"]+=1
                    continue
                stat["valid_rows"]+=1
                hour=timestamp.replace(minute=0,second=0,microsecond=0)
                selected=groups[taxon][animal]
                selected[hour]=choose_from_timestamp(selected.get(hour),(timestamp,lat,lon))
    return groups,source_counts,other_taxa

def analyze_from_group(animals,source_count):
    """Invoke unchanged source-locked Northern ecology estimator without raw export."""
    original=north.load_events
    clean={name:sorted(v.values()) for name,v in animals.items()}
    n_hourly=sum(len(x) for x in clean.values())
    def source_loader(_filename):
        return clean,source_count["rows"],source_count["invalid_rows"]
    try:
        north.load_events=source_loader
        results=north.analyze_file(Path("already_provider_md5_verified_raw_source.csv"))
    finally:
        north.load_events=original
    return {"native_records":source_count["rows"],"native_valid_records":source_count["valid_rows"],
            "native_invalid_records":source_count["invalid_rows"],
            "hourly_time_only_fixes":n_hourly,"original_individuals":len(clean),
            **results}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract["version"]!="utah-four-taxon-time-only-hourly-solar-ecology-v0":
        raise ValueError("Missing frozen source and estimand")
    src=contract["source"]
    registered=json.loads(CATALOG.read_text(encoding="utf-8"))["packages"]
    matched=[x for x in registered if x["package_uuid"]==src["package_uuid"]]
    if len(registered)!=437 or len(matched)!=1 or set(matched[0]["scientific_names"])!=set(src["catalog_taxa"]):
        raise ValueError("Frozen full Movebank discovery frame changed")
    result={"source":"Utah ungulates UDWR, original published Movebank study","doi":src["doi"],
            "source_scope":"one multi-taxon study, not a set of independent ecosystems","taxa":[]}
    native=args.out/"original_provider.zip"
    try:
        files=original_files(src["package_uuid"])
        original=[x for x in files if x["bitstream_uuid"]==src["original_bitstream_uuid"]]
        if len(original)!=1 or original[0]["checksum"]["value"].lower()!=src["original_md5"].lower() or original[0]["bytes"]!=src["original_bytes"]:
            raise ValueError("Provider original source checksum, UUID or size changed")
        result["provider_original_md5_verified"]=checksum_and_download(original[0],native)
        groups,counts,other=extract_time_only_original_source(native,src["catalog_taxa"])
        result["nonmatching_or_missing_taxon_records"]=other
        for taxon in src["catalog_taxa"]:
            effect=analyze_from_group(groups[taxon],counts[taxon])
            result["taxa"].append({"taxon":taxon,**effect})
            print("UTAH_UGULATE_SOLAR_ECOLOGY "+json.dumps(result["taxa"][-1],sort_keys=True),flush=True)
        result["status"]="source_sample_and_effects_evaluated"
    except Exception as ex:
        result.update(status="source_hold",error=f"{type(ex).__name__}: {ex}")
        # Mandatory report of all original four taxa, not zero or selective absence.
        if not result["taxa"]:
            result["taxa"]=[{"taxon":t,"effect_status":"source_hold","effect":None} for t in src["catalog_taxa"]]
    finally:
        native.unlink(missing_ok=True)
    (args.out/"utah_four_taxa_original_results.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("UTAH_FOUR_TAXA_SUMMARY "+json.dumps({
        "status":result["status"],"total_fixed_species":4,
        "admitted_taxa":sum(t.get("effect_status")=="exploratory_population_description" for t in result["taxa"]),
        "unavailable_or_hold":sum(t.get("effect_status")!="exploratory_population_description" for t in result["taxa"])
    },sort_keys=True),flush=True)
if __name__=="__main__":main()
