"""Original-data shared space×season×solar-hour taxon contrasts, 10 preselected sources.

Post-individual-result exploratory ecological estimand, not prior confirmation.
Do not print GPS coordinates, source animal IDs, cell IDs or original timestamps.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from itertools import combinations
from datetime import datetime
import json,math
from pathlib import Path
from statistics import mean

from scripts.movebank_native_ecology_20261019 import (
    HERE,original_files,checksum_and_download
)
from scripts.global_solar_azimuth_12_new_original_events_v1 import (
    load_source_taxa
)
from scripts.solar_azimuth_macro_v0 import directional_step

CONTRACT=HERE/"research/GLOBAL_SOLAR_AZIMUTH_MULTI_SOURCE_SHARED_CELL_V0_CONTRACT.json"
SOURCE=HERE/"research/GLOBAL_SOLAR_AZIMUTH_NEW24_PROVIDER_FROZEN_SOURCE_FILE_MANIFEST_20261025.json"

MIN_CELL_ANIMALS=3
MIN_CELL_STEPS=15
MIN_CELL_DAYS=3
MIN_PAIR_CELLS=3


def cell_for_step(step,first,second):
    lat=(first[1]+second[1])/2
    lon=((first[2]+((second[2]-first[2]+180)%360-180)/2+180)%360)-180
    return (math.floor(lat),math.floor(lon),step.solar_date.year,
            step.solar_date.month,int(step.solar_hour//4))


def admit_source_taxon_cells(tracks):
    """Return ephemeral keyed original data only; never export cell keys."""
    internal=defaultdict(lambda:{"animals":defaultdict(lambda:[0.0,0]),
                                 "dates":set(), "steps":0})
    for ind,hour_fixes in tracks.items():
        prev=None
        for cur in sorted(hour_fixes.values()):
            if prev is not None:
                step=directional_step(prev,cur)
                if step is not None:
                    key=cell_for_step(step,prev,cur)
                    s=internal[key]
                    v=s["animals"][ind]
                    v[0]+=math.cos(math.radians(step.bearing-step.sun_azimuth))
                    v[1]+=1
                    s["dates"].add(step.solar_date)
                    s["steps"]+=1
            prev=cur
    admitted={}
    for key,value in internal.items():
        if (len(value["animals"])<MIN_CELL_ANIMALS
                or len(value["dates"])<MIN_CELL_DAYS
                or value["steps"]<MIN_CELL_STEPS):
            continue
        animal_means=[v[0]/v[1] for v in value["animals"].values() if v[1]>0]
        admitted[key]={"animal_equal_mean":mean(animal_means),
                       "n_animals":len(animal_means),
                       "source_animal_ids":set(value["animals"]),
                       "source_days":value["dates"],
                       "eligible_steps":value["steps"]}
    return admitted


def source_pair_comparisons(source_taxon_cells, all_native_taxa):
    """All unordered pairs, including unsupported. No post-result pair filtering."""
    results=[]
    for aa,bb in combinations(sorted(set(all_native_taxa)),2):
        a=source_taxon_cells.get(aa,{})
        b=source_taxon_cells.get(bb,{})
        both=sorted(set(a)&set(b))
        result={"taxa":[aa,bb],
                "source_eligible_species_A_cells":len(a),
                "source_eligible_species_B_cells":len(b),
                "shared_source_grid_month_solar_hour_cells":len(both),
                "status":"NO_COMMON_3_CELL_SUPPORT",
                "a_minus_b_solar_relative_bearing_cosine":None}
        if len(both)>=MIN_PAIR_CELLS:
            values=[a[k]["animal_equal_mean"]-b[k]["animal_equal_mean"] for k in both]
            result.update({
                "status":"SUPPORTED_SOURCE_DESCRIPTIVE",
                "a_minus_b_solar_relative_bearing_cosine":mean(values),
                "a_shared_cell_mean_cos":mean(a[k]["animal_equal_mean"] for k in both),
                "b_shared_cell_mean_cos":mean(b[k]["animal_equal_mean"] for k in both),
                "shared_unique_coarse_1degree_spatial_grids":len({k[:2] for k in both}),
                "shared_year_month_combinations":len({k[2:4] for k in both}),
                "shared_solar_clock_4h_categories":len({k[4] for k in both}),
                "eligible_tagged_animals_species_A":len(set.union(*(a[k]["source_animal_ids"] for k in both))),
                "eligible_tagged_animals_species_B":len(set.union(*(b[k]["source_animal_ids"] for k in both))),
                "number_unique_source_solar_dates":len(set.union(*(a[k]["source_days"]|b[k]["source_days"] for k in both))),
                "n_original_gps_steps_species_A_cells_sum":sum(a[k]["eligible_steps"] for k in both),
                "n_original_gps_steps_species_B_cells_sum":sum(b[k]["eligible_steps"] for k in both)
            })
        results.append(result)
    return results


def source_preselection():
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    m=json.loads(SOURCE.read_text(encoding="utf-8"))
    if contract["version"]!="global-solar-azimuth-original-multitaxon-shared-cell-v0":
        raise ValueError("Shared-cell ecological contract changed")
    selected=[s for s in m["source_file_entries"]
              if s["sample_stratum"]=="all_remaining_multitaxon_census"]
    if len(selected)!=10 or any(len(set(s["original_species_labels"]))<2 for s in selected):
        raise ValueError("Original full 10-source multispecies frame was altered")
    return selected


def evaluate_source(entry,out):
    original=entry["original_file"]
    report={
        "package_uuid":entry["package_uuid"],
        "original_dois":entry["original_dois"],
        "original_species_labels":entry["original_species_labels"],
        "source_status":"SOURCE_HOLD",
        "shared_taxon_pairs":[],
        "original_cell_coordinates_exported":False
    }
    native=out/("private_"+entry["package_uuid"]+".csv")
    try:
        files=[f for f in original_files(entry["package_uuid"])
               if f["bitstream_uuid"]==original["bitstream_uuid"]]
        if len(files)!=1 or files[0]["bytes"]!=original["bytes"] or files[0]["checksum"]!=original["checksum"]:
            raise ValueError("Source original UUID, checksum or file size changed")
        report["verified_original_provider_checksum"]=checksum_and_download(files[0],native)
        taxa,coverage,metadata=load_source_taxa(native,original["filename"],entry["original_species_labels"])
        report["original_total_rows"]=metadata["original_total_rows"]
        admitted={}
        for taxon in entry["original_species_labels"]:
            admitted[taxon]=admit_source_taxon_cells(taxa[taxon])
            taxa[taxon].clear()
        report["shared_taxon_pairs"]=source_pair_comparisons(admitted,entry["original_species_labels"])
        report["source_status"]="source_qualified_all_pairs_evaluated"
    except Exception as exc:
        report["reason"]=f"{type(exc).__name__}: {str(exc)[:160]}"
        report["shared_taxon_pairs"]=[
            {"taxa":[aa,bb],"status":"SOURCE_HOLD","a_minus_b_solar_relative_bearing_cosine":None}
            for aa,bb in combinations(sorted(set(entry["original_species_labels"])),2)]
    finally:
        native.unlink(missing_ok=True)
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--shard",required=True,type=int,choices=(0,1,2,3,4))
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    all_sources=source_preselection()
    values=[]
    for i,entry in enumerate(all_sources):
        if i%5!=args.shard:
            continue
        result=evaluate_source(entry,args.out)
        values.append(result)
        print("SOLAR_AZIMUTH_SHARED_CELL_SOURCE "+
              json.dumps(result,sort_keys=True,ensure_ascii=False),flush=True)
    if len(values)!=2:raise ValueError("Each shard requires two original studies")
    report={
        "scope":"All fixed v2 multi-source register taxa, same 1degree grid/yearmonth/4h solar-time support; GPS cell identities not emitted.",
        "source_originals":values,
        "selected_original_source_count":2,
        "source_verified_count":sum(x["source_status"]=="source_qualified_all_pairs_evaluated" for x in values),
        "n_source_taxon_pair_supported":sum(y["status"]=="SUPPORTED_SOURCE_DESCRIPTIVE"
                                           for x in values for y in x["shared_taxon_pairs"]),
        "n_source_taxon_pair_unsupported":sum(y["status"]!="SUPPORTED_SOURCE_DESCRIPTIVE"
                                           for x in values for y in x["shared_taxon_pairs"]),
        "fixed_after_old_marginal_outcomes":"exploratory; do not treat as confirmatory"
    }
    (args.out/("solar_azimuth_shared_cell_shard_"+str(args.shard)+".json")).write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("SOLAR_AZIMUTH_SHARED_CELL_SUMMARY "+
          json.dumps({k:v for k,v in report.items() if k!="source_originals"},sort_keys=True),flush=True)


if __name__=="__main__":
    main()
