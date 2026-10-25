"""First independent NEW original Movebank GPS samples: 12 fixed registry sources.

Source choice, exact original bitstream and MD5, and the four initial metadata
HOLDS were fixed WITHOUT any NEW animal displacement outcome. No replacement.
Returns source×taxon aggregate azimuth outcomes only, never GPS coordinates,
individual IDs, precise UTC observations or original file bytes.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
import gzip
import io
import json
import math
from pathlib import Path
from zipfile import ZipFile, BadZipFile

from scripts.movebank_native_ecology_20261019 import (
    HERE, original_files, checksum_and_download, parse_time
)
from scripts.movebank_utah_four_taxa_solar_20261019 import choose_from_timestamp
from scripts.solar_azimuth_macro_v0 import analyze_taxon

MANIFEST = HERE / "research/GLOBAL_SOLAR_AZIMUTH_12_NEW_SOURCE_FROZEN_ORIGINAL_FILE_MANIFEST_20261025.json"
CONTRACT = HERE / "research/GLOBAL_SOLAR_AZIMUTH_INDEPENDENT_12SOURCE_V1_CONTRACT.json"
MAX_ROWS = 2_000_000
MAX_ORIGINAL_FILE_BYTES = 120_000_000
MAX_UNCOMPRESSED_CSV = 300_000_000


class StrictSourceHold(ValueError):
    pass


def check_manifest():
    m=json.loads(MANIFEST.read_text(encoding="utf-8"))
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    if m.get("version")!=c.get("version") or len(m["sample_original_file_source_entries"])!=12:
        raise ValueError("Frozen sample/contract not reproducible")
    sample=m["sample_original_file_source_entries"]
    if sum(x["status"]=="ORIGINAL_FILE_METADATA_ADMISSIBLE" for x in sample)!=8:
        raise ValueError("First blind original provider file qualification changed")
    if sum(x["status"]=="SOURCE_HOLD" for x in sample)!=4:
        raise ValueError("Original four source metadata HOLDs changed")
    if len({x["package_uuid"] for x in sample})!=12:
        raise ValueError("Duplicate frozen original sample")
    if set(x["package_uuid"] for x in sample) & set(c["previous_sources"]):
        raise ValueError("New source overlaps previous original archives")
    if sum(x["sample_stratum"]==g for x in sample for g in
           ("single_large","single_small","multiple_large","multiple_small"))!=12:
        raise ValueError("Invalid original strata")
    return sample


def normalized_columns(fields):
    result={}
    for value in fields or []:
        key=str(value).strip().lower()
        if key in result:
            raise StrictSourceHold("Duplicate column after case-fold/whitespace normalization")
        result[key]=value
    return result


def primary_csv_stream(path, original_name):
    """Only the single explicitly selected original file. No ZIP path extraction."""
    suffix=original_name.lower()
    if suffix.endswith(".zip"):
        with ZipFile(path) as z:
            found=[
                v for v in z.infolist()
                if not v.is_dir() and v.filename.lower().endswith(".csv")
                and "reference-data" not in v.filename.lower()
                and "__macosx" not in v.filename.lower()
                and not v.filename.rsplit("/",1)[-1].startswith("._")
            ]
            if len(found)!=1:
                raise StrictSourceHold("ZIP must contain exactly one primary original CSV")
            member=found[0]
            if not (64<=member.file_size<=MAX_UNCOMPRESSED_CSV):
                raise StrictSourceHold("ZIP extracted original CSV exceeds frozen source size cap")
            with z.open(member) as raw:
                with io.TextIOWrapper(raw,encoding="utf-8-sig",errors="replace",newline="") as source:
                    yield source
    elif suffix.endswith(".csv.gz"):
        with gzip.open(path,"rb") as raw:
            with io.TextIOWrapper(raw,encoding="utf-8-sig",errors="replace",newline="") as source:
                yield source
    elif suffix.endswith(".csv"):
        with path.open("r",encoding="utf-8-sig",errors="replace",newline="") as source:
            yield source
    else:
        raise StrictSourceHold("Not one of three frozen original source data formats")


def load_source_taxa(path, source_name, registry_taxa):
    """Read source tracks on sealed ephemeral CI disk; return only local objects."""
    taxa=list(dict.fromkeys(str(x).strip() for x in registry_taxa))
    if not taxa or any(not x for x in taxa):
        raise StrictSourceHold("No exact taxonomy from original source catalog")
    status={taxon:{"original_taxon_rows":0, "invalid_rows":0,
                   "hour_selected_fixes":0, "source_individuals":0} for taxon in taxa}
    track={taxon:defaultdict(dict) for taxon in taxa}
    total=invalid=taxon_unknown=0
    csv.field_size_limit(10_000_000)

    for input_stream in primary_csv_stream(path,source_name):
        rd=csv.DictReader(input_stream)
        fields=normalized_columns(rd.fieldnames)
        required=("timestamp","individual-local-identifier","location-lat","location-long")
        missing=[key for key in required if key not in fields]
        if missing:
            raise StrictSourceHold("Frozen original source GPS schema missing: "+",".join(missing))
        original_taxon_col=fields.get("individual-taxon-canonical-name")
        if original_taxon_col is None and len(taxa)>1:
            raise StrictSourceHold("Multi-species source lacks native taxon column")
        for line in rd:
            total+=1
            if total>MAX_ROWS:
                raise StrictSourceHold("Original source >2m rows capped before effect; no truncated analysis")
            if original_taxon_col is None:
                taxon=taxa[0]
            else:
                taxon=(line.get(original_taxon_col) or "").strip()
                if taxon not in track:
                    taxon_unknown+=1
                    continue
            st=status[taxon]
            st["original_taxon_rows"]+=1
            t=parse_time(line.get(fields["timestamp"],""))
            ind=(line.get(fields["individual-local-identifier"]) or "").strip()
            try:
                lat=float(line.get(fields["location-lat"]))
                lon=float(line.get(fields["location-long"]))
            except (ValueError,TypeError):
                lat=float("nan");lon=float("nan")
            if t is None or not ind or not (math.isfinite(lat) and math.isfinite(lon)
                                            and -90<=lat<=90 and -180<=lon<=180):
                st["invalid_rows"]+=1
                invalid+=1
                continue
            hour=t.replace(minute=0,second=0,microsecond=0)
            selected=track[taxon][ind]
            selected[hour]=choose_from_timestamp(selected.get(hour),(t,lat,lon))

    for taxon in taxa:
        status[taxon]["source_individuals"]=len(track[taxon])
        status[taxon]["hour_selected_fixes"]=sum(len(v) for v in track[taxon].values())
    return track,status,{"original_total_rows":total,"invalid_position_time_or_id_rows":invalid,
                         "source_rows_outside_registered_taxa":taxon_unknown,
                         "original_UTC_attestation":"source timestamps parsed as UTC under the original Movebank archive convention; independent device-clock attestation not supplied"}


def analyze_original_source(entry, out):
    """Never replace source, taxon or original primary file after seeing rows."""
    result={
        "package_uuid":entry["package_uuid"],
        "dois":entry["original_dois"],
        "source_study_ids":entry["source_study_ids"],
        "registry_species_labels":entry["original_species_labels"],
        "original_licenses":entry["original_licenses"],
        "sample_stratum":entry["sample_stratum"],
        "metadata_selection_rank":entry["within_stratum_metadata_rank"],
        "source_state":"SOURCE_HOLD",
        "original_file_size":entry["original_file"]["bytes"] if entry["original_file"] else None,
        "source_taxa":[],
    }
    for taxon in entry["original_species_labels"]:
        result["source_taxa"].append({
            "taxon":taxon,"result_status":"SOURCE_HOLD","qualified_individuals":0
        })
    if entry["status"]=="SOURCE_HOLD":
        result["reason"]="FROZEN_SOURCE_METADATA_HOLD: "+str(entry.get("hold_reason") or "")
        return result
    orig=entry["original_file"]
    target=out/("private_source_"+entry["package_uuid"]+(".zip" if orig["filename"].lower().endswith(".zip") else ".csv"))
    try:
        matches=[x for x in original_files(entry["package_uuid"])
                 if x["bitstream_uuid"]==orig["bitstream_uuid"]]
        if len(matches)!=1:
            raise StrictSourceHold("Original source bitstream UUID no longer unique")
        p=matches[0]
        if p["bytes"]!=orig["bytes"] or p["bytes"]>MAX_ORIGINAL_FILE_BYTES:
            raise StrictSourceHold("Provider original byte count changed")
        if p["checksum"]!=orig["checksum"]:
            raise StrictSourceHold("Original provider checksum changed")
        verification=checksum_and_download(p,target)
        result["original_provider_checksum_verified"]=verification
        track,coverage,extra=load_source_taxa(target,orig["filename"],entry["original_species_labels"])
        result["source_original_coverage"]=extra
        result["source_taxa"]=[]
        for taxon in entry["original_species_labels"]:
            st=coverage[taxon]
            if st["original_taxon_rows"]==0:
                stats={"status":"NO_SOURCE_TAXON_RECORDS",
                       "supported_individuals":0, "daylight_directional_qualified_steps":0,
                       "results":None}
            else:
                stats=analyze_taxon({animal:list(events.values())
                                     for animal,events in track[taxon].items()})
            result["source_taxa"].append({
                "taxon":taxon, "source_original_coverage":st, "analysis":stats,
                "result_status":stats["status"], "qualified_individuals":stats["supported_individuals"]
            })
            track[taxon].clear()
        result["source_state"]="original_MD5_verified_source_analyzed"
    except Exception as exc:
        # Avoid representing missing or invalid source as ecological null.
        result["reason"]=f"{type(exc).__name__}: {str(exc)[:200]}"
        result["source_state"]="SOURCE_HOLD"
        result["source_taxa"]=[{"taxon":taxon,"result_status":"SOURCE_HOLD",
                                "qualified_individuals":0}
                               for taxon in entry["original_species_labels"]]
    finally:
        target.unlink(missing_ok=True)
    return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--shard",required=True,type=int,choices=(0,1,2))
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    sources=check_manifest()
    rows=[]
    for i,x in enumerate(sources):
        if i%3!=args.shard:
            continue
        record=analyze_original_source(x,args.out)
        rows.append(record)
        print("SOLAR_AZIMUTH_V1_NEW_SOURCE "+
              json.dumps(record,ensure_ascii=False,sort_keys=True),flush=True)
    assert len(rows)==4
    report={
        "schema":"global-azimuth-prospective-independent-source-frame-v1",
        "shard":args.shard,"n_assigned_registered_sources":4,
        "n_source_originals_MD5_analyzed":sum(x["source_state"]=="original_MD5_verified_source_analyzed" for x in rows),
        "n_source_HOLD":sum(x["source_state"]=="SOURCE_HOLD" for x in rows),
        "n_source_taxon_admitted":sum(t.get("result_status")=="descriptive_source_estimated"
                                      for x in rows for t in x["source_taxa"]),
        "source_data":rows,
        "claim_ceiling":"Original Movebank GPS observations within fixed sample only; not causal solar compass, global animal law or independent biome inference. Raw records never distributed."
    }
    (args.out/("azimuth_new_original_source_v1_shard_"+str(args.shard)+".json")).write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SOLAR_AZIMUTH_V1_SHARD_SUMMARY "+
          json.dumps({k:v for k,v in report.items() if k!="source_data"},sort_keys=True),
          flush=True)


if __name__=="__main__":
    main()
