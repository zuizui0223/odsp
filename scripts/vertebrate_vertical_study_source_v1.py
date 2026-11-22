#!/usr/bin/env python3
"""Basham et al. tropical vertebrate 62-study source-only design admission.

Parses only study, taxon, vertical geometry & endpoint *labels*.
No richness/abundance numerical source responses are converted or summarized.
"""
from __future__ import annotations
import csv
from collections import Counter,defaultdict
import hashlib
import io
import json
from pathlib import Path
from urllib.request import Request,urlopen

SOURCE_REPO="schefferslab/Vert-Strata-Meta"
SOURCE_COMMIT="a68a2fca81407800855ea482f94104b425911232"
SOURCE_PATH="data/stripped_data/analysis/data_joined.csv"
SOURCE_GIT_BLOB="7b9c5b7e2b5722c7f4891853dc4fbc2e83db6b4c"
SOURCE_URL=f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}/{SOURCE_PATH}"
FILE_BYTE_CEILING=2_000_000
STRUCT_COLUMNS=(
    "link","study_id","study_id.x","taxa","biodiversity_metric",
    "strata_category","mean_strata_height_p","min_strata_height",
    "max_strata_height","country","continent",
    "temporal_effort_at_each_height","spatial_effort_unit",
    "season","elevation","canopy_height"
)
SEALED_RESPONSE_COLUMNS=(
    "corrected_biodiversity_metric_value","biodiversity_metric_value",
    "max_richness","max_abundance","subsequent_correction",
    "biodiversity_metric_corrected"
)

def git_blob_hash(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

def source_structure(raw):
    if git_blob_hash(raw)!=SOURCE_GIT_BLOB:
        raise RuntimeError("original pinned Git blob identity mismatch")
    try: decoded=raw.decode("utf-8-sig")
    except UnicodeError: decoded=raw.decode("latin-1")
    reader=csv.DictReader(io.StringIO(decoded,newline=""))
    fields=reader.fieldnames or []
    if len(fields)!=len(set(fields)) or not set(STRUCT_COLUMNS).issubset(fields):
        raise RuntimeError("original source design field roster changed")
    if not set(SEALED_RESPONSE_COLUMNS).issubset(fields):
        raise RuntimeError("frozen numerical response columns absent")
    units=defaultdict(lambda:{"heights":set(),"strata":set(),"study":None,
                              "taxa":None,"endpoint":None,"rows":0})
    counts_taxa=Counter()
    counts_metric=Counter()
    blank_keys=Counter()
    invalid_height_geometry=0
    nrows=0
    site_study_taxa={}
    for row in reader:
        # Read only design keys, not any biological numeric outcome.
        s={f:row.get(f,"").strip() for f in STRUCT_COLUMNS}
        nrows+=1
        for f in ("link","study_id","taxa","biodiversity_metric","strata_category"):
            if not s[f] or s[f]=="NA":
                blank_keys[f]+=1
        counts_taxa[s["taxa"]]+=1
        counts_metric[s["biodiversity_metric"]]+=1
        group=(s["link"],s["biodiversity_metric"])
        unit=units[group]
        if unit["study"] not in (None,s["study_id"]) or unit["taxa"] not in (None,s["taxa"]):
            raise RuntimeError("source site×metric refers to conflicting studies/taxa")
        unit["study"]=s["study_id"]
        unit["taxa"]=s["taxa"]
        unit["endpoint"]=s["biodiversity_metric"]
        unit["rows"]+=1
        unit["strata"].add(s["strata_category"])
        try:
            # This is an OBSERVATION-HEIGHT covariate, not original richness/abundance.
            h=float(s["mean_strata_height_p"])
            if not (h==h and -1e-9 <=h<=1.000000001):
                invalid_height_geometry+=1
            else: unit["heights"].add(round(h,8))
        except Exception:
            invalid_height_geometry+=1
        if s["link"] in site_study_taxa and site_study_taxa[s["link"]]!=(s["study_id"],s["taxa"]):
            raise RuntimeError("site identifier reused across study/taxon")
        site_study_taxa[s["link"]]=(s["study_id"],s["taxa"])
    if not nrows:
        raise RuntimeError("empty source rows")
    source_studies={u["study"] for u in units.values()}
    site_metric_2plus=[u for u in units.values() if len(u["heights"])>=2]
    site_metric_3plus=[u for u in units.values() if len(u["heights"])>=3]
    taxa_metric_studies=defaultdict(set)
    taxa_metric_units=Counter()
    for u in site_metric_2plus:
        key=(u["taxa"],u["endpoint"])
        taxa_metric_studies[key].add(u["study"])
        taxa_metric_units[key]+=1
    eligible=[{"taxa":key[0],"metric":key[1],"distinct_studies":len(v),
               "site_metric_units_with_ge2_heights":taxa_metric_units[key]}
              for key,v in sorted(taxa_metric_studies.items())
              if len(v)>=4]
    all_qualified_studies={study for key,v in taxa_metric_studies.items()
                           if len(v)>=4 for study in v}
    # v1.1: categorical strata_category is optional.
    # The quantitative height geometry is mean_strata_height_p.
    required_blank={key:blank_keys[key] for key in
                    ("link","study_id","taxa","biodiversity_metric")
                    if blank_keys[key]>0}
    units_with_duplicate_numeric_heights=sum(
        unit["rows"]>len(unit["heights"]) for unit in units.values())
    redundant_height_rows=sum(
        max(0,unit["rows"]-len(unit["heights"])) for unit in units.values())
    accepted=(len({r["taxa"] for r in eligible})>=3
              and len(all_qualified_studies)>=15
              and not required_blank
              and invalid_height_geometry==0)
    return {
        "status":"source_structure_admitted_numerical_biodiversity_sealed" if accepted else "source_architecture_gate_hold",
        "source_repo":SOURCE_REPO,
        "source_commit":SOURCE_COMMIT,
        "source_git_blob_sha1":SOURCE_GIT_BLOB,
        "source_file_sha256":hashlib.sha256(raw).hexdigest(),
        "source_file_bytes":len(raw),
        "source_rows":nrows,
        "source_unique_studies":len(source_studies),
        "source_site_identifiers":len(site_study_taxa),
        "source_site_metric_units":len(units),
        "site_metric_units_ge2_heights":len(site_metric_2plus),
        "site_metric_units_ge3_heights":len(site_metric_3plus),
        "source_taxa_row_counts":dict(counts_taxa),
        "source_metric_row_counts":dict(counts_metric),
        "taxon_endpoint_eligible_study_cohorts":eligible,
        "all_cohort_qualified_distinct_studies":len(all_qualified_studies),
        "structural_blank_key_counts":dict(blank_keys),
        "required_blank_key_counts":required_blank,
        "optional_textual_strata_category_blank_rows":blank_keys["strata_category"],
        "numeric_height_is_authoritative_not_strata_category_text":True,
        "site_metric_units_with_repeated_numeric_height":units_with_duplicate_numeric_heights,
        "redundant_site_metric_height_rows":redundant_height_rows,
        "v1_first_result_preserved_as_structural_hold":True,
        "invalid_height_geometry_rows":invalid_height_geometry,
        "original_biodiversity_numeric_values_inspected":False,
        "no_species_id_or_independent_biological_detection_calibration":True,
    }

def main():
    receipt={"source_repo":SOURCE_REPO,"source_commit":SOURCE_COMMIT,
             "original_biodiversity_numeric_values_inspected":False}
    try:
        req=Request(SOURCE_URL,headers={"User-Agent":"ODSP-vertebrate-source-only-v1/1.0"})
        with urlopen(req,timeout=90) as response:
            raw=response.read(FILE_BYTE_CEILING+1)
        if len(raw)>FILE_BYTE_CEILING:
            raise RuntimeError("published source exceeds frozen maximum")
        receipt=source_structure(raw)
    except Exception as exc:
        receipt.update({"status":"source_access_or_schema_stop",
                        "exception":type(exc).__name__,
                        "reason":str(exc)[:350]})
    path=Path("results/vertebrate_vertical_study_source_v1.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
