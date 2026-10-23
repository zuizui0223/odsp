"""Independent Wyoming published ORIGINAL GPS: same diel source estimand as Utah.

Both registered mammals mandatory. Only source group and coarse paired-study
summaries leave the runner, never GPS fixes, animal IDs or calendar timestamps.
"""
import argparse,csv,json,math,random
from collections import defaultdict
from pathlib import Path
from statistics import mean
from scripts.movebank_native_ecology_20261019 import (
    HERE,original_files,checksum_and_download,parse_time
)
from scripts.movebank_utah_four_taxa_solar_20261019 import choose_from_timestamp
from scripts.movebank_utah_diel_photoperiod_20261019 import one_taxon,compare_sites
from scripts.movebank_utah_shared_spatial_20261019 import cluster_interval

CONTRACT=HERE/"research/MOVEBANK_WYOMING_TWO_UNGULATES_SOURCE_V0_20261022.json"
CATALOG=HERE/"research/seasonal_database_catalog/2026-10-19/movebank/catalog.json"

def streaming_time_selected_csv(path,registered_taxa):
    species={taxon:defaultdict(dict) for taxon in registered_taxa}
    counts={taxon:{"source_rows":0,"invalid_source_rows":0,"valid_source_rows":0} for taxon in registered_taxa}
    unclassified=0
    with path.open("r",encoding="utf-8-sig",newline="") as file:
        r=csv.DictReader(file)
        fields={c.lower().strip():c for c in (r.fieldnames or [])}
        required=("timestamp","individual-local-identifier","location-lat","location-long","individual-taxon-canonical-name")
        if not all(f in fields for f in required):
            raise ValueError("Original published source lacks one or more registered GPS/taxon fields")
        for row in r:
            taxon=(row.get(fields["individual-taxon-canonical-name"]) or "").strip()
            if taxon not in species:
                unclassified+=1;continue
            stats=counts[taxon];stats["source_rows"]+=1
            animal=(row.get(fields["individual-local-identifier"]) or "").strip()
            stamp=parse_time(row.get(fields["timestamp"],""))
            try:lat=float(row[fields["location-lat"]]);lon=float(row[fields["location-long"]])
            except (ValueError,TypeError,KeyError):lat=lon=float("nan")
            if stamp is None or not animal or not(math.isfinite(lat) and math.isfinite(lon) and abs(lat)<=90 and abs(lon)<=180):
                stats["invalid_source_rows"]+=1;continue
            stats["valid_source_rows"]+=1
            bucket=stamp.replace(minute=0,second=0,microsecond=0)
            selected=species[taxon][animal]
            selected[bucket]=choose_from_timestamp(selected.get(bucket),(stamp,lat,lon))
    return species,counts,unclassified

def between_taxon_geography(spatial):
    taxon=list(spatial.keys())
    assert len(taxon)==2
    a,b=taxon
    base=compare_sites(spatial)
    if len(base)!=1:raise ValueError("Exact original two-species paired source comparison missing")
    row=base[0]
    common=sorted(set(spatial[a])&set(spatial[b]))
    group=defaultdict(list)
    for lat,lon,year,month in common:
        group[(lat,lon)].append(spatial[a][(lat,lon,year,month)]-spatial[b][(lat,lon,year,month)])
    blocks=[mean(v) for v in group.values()]
    return {
        "taxa":[a,b],
        "source_original_shared_coarse_cell_months":row["shared_1degree_calendar_month_cells"],
        "source_original_pair_estimate_if_at_least_three_months":row["diel_contrast_a_minus_b_on_common_cells"],
        "shared_distinct_coarse_geographic_1degree_blocks":len(blocks),
        "equal_geographic_block_mean_q_difference_a_minus_b":mean(blocks) if len(blocks)>=3 else None,
        "blockbootstrap_95_interval":cluster_interval(blocks),
        "q_difference_sign_if_estimable":("positive" if mean(blocks)>0 else "negative" if mean(blocks)<0 else "zero") if len(blocks)>=3 else "unavailable",
        "interpretation":"Original same-study coarse-month spatial overlap, not physically simultaneous behavior; independent of Utah field study but potentially overlapping other Wyoming GPS archives."
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    spec=json.loads(CONTRACT.read_text())
    if spec["version"]!="wyoming-two-ungulate-independent-source-diel-ecology-v0":raise ValueError("Source unregistered")
    src=spec["source"]
    catalog=json.loads(CATALOG.read_text())["packages"]
    if len(catalog)!=437:raise ValueError("Frozen 437-package frame missing")
    hits=[p for p in catalog if p["package_uuid"]==src["package_uuid"]]
    if len(hits)!=1 or set(hits[0]["scientific_names"])!=set(src["published_species"]):
        raise ValueError("Wrong registry species/source")
    report={
      "source_title":src["title"],"source_doi":src["doi"],"source_original_license":src["license"],
      "utah_previously_observed_reference_not_blinded":spec["utah_comparator"],
      "source_comparison_vs_Utah":"Independent public Wyoming source; no claim of independence from other Wyoming archives",
      "taxa":[],"paired_source_comparison":None
    }
    path=args.out/"wyoming_original.csv"
    try:
        matched=[f for f in original_files(src["package_uuid"]) if f["bitstream_uuid"]==src["original_bitstream_uuid"]]
        if len(matched)!=1 or matched[0]["checksum"]["value"].lower()!=src["original_md5"].lower() or matched[0]["bytes"]!=src["original_bytes"]:
            raise ValueError("Provider ORIGINAL source UUID, MD5 or byte count mismatch")
        report["source_integrity"]=checksum_and_download(matched[0],path)
        by_species,counts,other=streaming_time_selected_csv(path,src["published_species"])
        report["unclassified_source_rows"]=other
        locations={}
        for taxon in src["published_species"]:
            measured,spatial=one_taxon(taxon,by_species[taxon])
            measured["source_original_observations"]=counts[taxon]
            report["taxa"].append(measured)
            locations[taxon]=spatial
            by_species[taxon].clear()
            print("WYOMING_SAME_TAXA_DIEL_SOURCE "+json.dumps(measured,sort_keys=True),flush=True)
        report["paired_source_comparison"]=between_taxon_geography(locations)
        print("WYOMING_SAME_TAXA_COARSE_SPACE "+json.dumps(report["paired_source_comparison"],sort_keys=True),flush=True)
        report["status"]="two_original_wild_ungulate_taxa_processed"
    except Exception as e:
        report.update(status="source_hold",error=f"{type(e).__name__}: {e}")
        if not report["taxa"]:
            report["taxa"]=[{"taxon":name,"source_status":"source_hold","day_night_speed_contrast":None,"daylength_association":None} for name in src["published_species"]]
    finally:path.unlink(missing_ok=True)
    (args.out/"wyoming_mule_deer_bighorn_diel_ecology.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("WYOMING_SAME_TAXA_ECOLOGY_SUMMARY "+json.dumps({
      "status":report["status"],"source_species":len(report["taxa"]),
      "diel_effect_taxa":sum(x.get("day_night_speed_contrast") is not None for x in report["taxa"]),
      "daylength_slope_taxa":sum(x.get("daylength_association") is not None for x in report["taxa"]),
      "shared_source_gridmonths":(report["paired_source_comparison"] or {}).get("source_original_shared_coarse_cell_months",0)
    },sort_keys=True))
if __name__=="__main__":main()
