"""Original GPS solar-azimuth ecology on 24 NEW header-qualified sources.

Unlike prior convenience-source exploratory source groups, the source UUID list
is fixed by all-259 ORIGINAL CSV header provenance and registry-only SHA ranking.
No after-effect source substitution, no original individual tracks exported.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from scripts.movebank_native_ecology_20261019 import HERE
from scripts.global_solar_azimuth_12_new_original_events_v1 import analyze_original_source

CONTRACT=HERE/"research/GLOBAL_SOLAR_AZIMUTH_24_SCHEMA_QUALIFIED_NEW_SOURCE_V2_CONTRACT.json"
SOURCE_MANIFEST=HERE/"research/GLOBAL_SOLAR_AZIMUTH_NEW24_PROVIDER_FROZEN_SOURCE_FILE_MANIFEST_20261025.json"


def fixed_new_sources():
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    m=json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    if c["version"]!="global-solar-azimuth-all259-original-header-qualified-24-source-v2":
        raise ValueError("Prospective source frame changed")
    if m["version"]!=c["version"] or len(m["source_file_entries"])!=24:
        raise ValueError("First source-only provider MD5 preflight missing")
    sample=c["source_groups"]
    if [x["package_uuid"] for x in sample]!=[x["package_uuid"] for x in m["source_file_entries"]]:
        raise ValueError("Unpermitted original source roster substitution")
    for s,x in zip(sample,m["source_file_entries"]):
        if (x["status"]=="ORIGINAL_FILE_METADATA_ADMISSIBLE" and
                x["original_file"]["bytes"]!=s["expected_original_file_bytes"]):
            raise ValueError("Original provider size not frozen")
        if x["status"] not in ("ORIGINAL_FILE_METADATA_ADMISSIBLE","SOURCE_HOLD"):
            raise ValueError("Unrecognized pre-result original source status")
        if x["observed_original_GPS_rows"]!=0:
            raise ValueError("First source-only step leaked original GPS observations")
    return m["source_file_entries"]


def main():
    a=argparse.ArgumentParser()
    a.add_argument("--shard",type=int,choices=range(6),required=True)
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    source=fixed_new_sources()
    cohort=[]
    for idx,s in enumerate(source):
        if idx%6!=args.shard:continue
        result=analyze_original_source(s,args.out)
        result["source_design"]="v2_header_qualified_original_24_source_stratified_frame"
        cohort.append(result)
        print("SOLAR_AZIMUTH_V2_NEW_SOURCE "+
              json.dumps(result,sort_keys=True,ensure_ascii=False),flush=True)
    if len(cohort)!=4:
        raise ValueError("Expected four original source files per preselected shard")
    report={
        "version":"global-solar-azimuth-all259-original-header-qualified-24-source-v2",
        "sample_shard":args.shard,"preselected_original_packages_in_shard":4,
        "source_original_MD5_download_analyzed":sum(
            x["source_state"]=="original_MD5_verified_source_analyzed" for x in cohort),
        "source_HOLD_after_original_event_admission":sum(
            x["source_state"]=="SOURCE_HOLD" for x in cohort),
        "source_taxon_supported_effect_entries":sum(
            y.get("result_status")=="descriptive_source_estimated"
            for x in cohort for y in x["source_taxa"]),
        "source_originals":cohort,
        "interpretation":"Forthcoming original-source taxonomy/population tests are descriptive; no causal solar compass use, detection-effort equivalence or 24 independent ecological landscapes."
    }
    (args.out/("new_24_source_v2_shard_"+str(args.shard)+".json")).write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SOLAR_AZIMUTH_V2_SHARD_SUMMARY "+
          json.dumps({k:v for k,v in report.items() if k!="source_originals"},sort_keys=True),
          flush=True)


if __name__ == "__main__":
    main()
