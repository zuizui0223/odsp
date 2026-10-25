"""Original GPS × ERA5 100m wind and shortwave ecological geometry.

Two original co-sampled bird source studies chosen AFTER prior solar-only results.
All FOUR previously supported source-taxon pairs must replay exactly before
opening ANY hourly ERA5. No individual positions, cell IDs or UTC times exported.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime,timedelta
import json
import math
from pathlib import Path
from statistics import mean

from scripts.movebank_native_ecology_20261019 import (
    HERE,original_files,checksum_and_download
)
from scripts.global_solar_azimuth_12_new_original_events_v1 import load_source_taxa
from scripts.global_solar_azimuth_multitaxon_shared_cells_v0 import (
    admit_source_taxon_cells,cell_for_step,source_pair_comparisons
)
from scripts.solar_azimuth_macro_v0 import directional_step
from scripts.solar_azimuth_era5_wind_v0 import (
    get_original_hourly_response,validate_and_parse_weather,
    wind_flow_to,wrap_cos_degrees,year_request_parameters
)

CONTRACT=HERE/"research/SOLAR_WIND_IRRADIANCE_SHARED_GPS_V0_CONTRACT.json"
GPS_MANIFEST=HERE/"research/GLOBAL_SOLAR_AZIMUTH_NEW24_PROVIDER_FROZEN_SOURCE_FILE_MANIFEST_20261025.json"
REFERENCE=HERE/"research/GLOBAL_SOLAR_AZIMUTH_MULTITAXON_SHARED_CELL_COMBINED_FROZEN_V0_V1_20261025.json"
SOURCE_IDS={
   "8318572a-a9d8-4d9e-b685-7db8a73bdf86",
   "cd4e676d-424f-4b40-8e4e-3681a0f26530"
}
FIELDS=("solar_cos","windflow_cos","wind_sun_cos",
        "wind_speed_100m_ms","shortwave_W_m2","temperature_2m_C")


def original_setup():
    p=json.loads(CONTRACT.read_text(encoding="utf-8"))
    m=json.loads(GPS_MANIFEST.read_text(encoding="utf-8"))
    ref=json.loads(REFERENCE.read_text(encoding="utf-8"))
    if p["version"]!="original-shared-cell-solar-wind-irradiance-v0":
        raise ValueError("Frozen GPS×weather ecological contract not found")
    ids={r["uuid"] for r in p["exact_studies"]}
    if ids!=SOURCE_IDS or len(p["exact_studies"])!=2:
        raise ValueError("Outcome-independent original two-source roster was altered")
    sources={x["package_uuid"]:x for x in m["source_file_entries"]}
    previous={x["package_uuid"]:x for x in ref["all_original_multitaxon_source_results"]}
    if not ids<=sources.keys() or not ids<=previous.keys():
        raise ValueError("Frozen previous 10-original-source frame incomplete")
    if any(sources[i]["status"]!="ORIGINAL_FILE_METADATA_ADMISSIBLE" for i in ids):
        raise ValueError("Provider original source file cannot be used as registered")
    if any(previous[i]["source_status"]!="source_qualified_all_pairs_evaluated" for i in ids):
        raise ValueError("Previous original GPS pair not source-verified")
    pair_refs={}
    for pair in ref["supported_pair_results"]:
        if pair["source_package_uuid"] in ids:
            pair_refs.setdefault(pair["source_package_uuid"],[]).append(pair)
    for x in p["exact_studies"]:
        if len(pair_refs.get(x["uuid"],[]))!=x["expected_supported_pair_count"]:
            raise ValueError("Original 4-pair ecological support roster changed")
        if set(sources[x["uuid"]]["original_species_labels"])!=set(x["taxa"]):
            raise ValueError("Original source native taxa differ from registered source")
    return p,sources,pair_refs,previous


def preweather_replay(study,tracks,refs,previous):
    """Replay ALL source taxa + pair eligibility/means before weather access."""
    taxa=study["original_species_labels"]
    cells={taxon:admit_source_taxon_cells(tracks[taxon]) for taxon in taxa}
    replay=source_pair_comparisons(cells,taxa)
    frozen={(tuple(x["taxa"])):x for x in previous["shared_taxon_pairs"]}
    if len(frozen)!=len(replay) or set(tuple(x["taxa"]) for x in replay)!=set(frozen):
        raise ValueError("All preregistered original source taxon pairs changed")
    for item in replay:
        earlier=frozen[tuple(item["taxa"])]
        if (earlier["status"]!=item["status"] or
            earlier.get("shared_source_grid_month_solar_hour_cells")
              !=item.get("shared_source_grid_month_solar_hour_cells")):
            raise ValueError("Original source paired GPS support no longer replays")
        if item["status"]=="SUPPORTED_SOURCE_DESCRIPTIVE":
            value=item["a_minus_b_solar_relative_bearing_cosine"]
            if abs(value-earlier["a_minus_b_solar_relative_bearing_cosine"])>1e-10:
                raise ValueError("Original solar-only species contrast changed")
    target={tuple(x["taxa"]) for x in refs}
    live={tuple(x["taxa"]) for x in replay if x["status"]=="SUPPORTED_SOURCE_DESCRIPTIVE"}
    if live!=target:
        raise ValueError("New weather analysis must cover exactly original supported pairs")
    return cells,replay


def sampled_original_steps(tracks,eligible_cells):
    """Ephemeral signed original travel headings and UTC hours for weather linking."""
    out=defaultdict(list)
    for taxon,wanted in eligible_cells.items():
        if not wanted:
            continue
        for individual,selected in tracks[taxon].items():
            fixes=sorted(selected.values())
            for prior,next_fix in zip(fixes,fixes[1:]):
                step=directional_step(prior,next_fix)
                if step is None:
                    continue
                cell=cell_for_step(step,prior,next_fix)
                if cell not in wanted:
                    continue
                mid=prior[0]+(next_fix[0]-prior[0])/2
                utc=mid.replace(minute=0,second=0,microsecond=0)
                out[taxon].append({
                    "animal":individual,
                    "cell":cell,
                    "utc_hour":utc,
                    "bearing":step.bearing,
                    "sun_azimuth":step.sun_azimuth
                })
    return out


def query_frame(rows):
    keys=set()
    for events in rows.values():
        for x in events:
            c=x["cell"]
            keys.add((c[0],c[1],x["utc_hour"].year))
    return sorted(keys)


def get_weather(frame, max_gridyears):
    if not frame or len(frame)>max_gridyears:
        raise ValueError("Original source requires unsupported number of grid-years")
    result={}
    receipts=[]
    for lat,lon,year in frame:
        parameters=year_request_parameters(lat,lon,year)
        raw=get_original_hourly_response(parameters)
        weather,receipt=validate_and_parse_weather(raw,year)
        result[(lat,lon,year)]=weather
        # Receipt does not contain actual animal location/UTC time/year or URL.
        receipts.append(receipt)
    return result,receipts


def matched_cell_stats(events,weather, eligible):
    """Original animal-equal per-cell vector means on identical sampled steps."""
    per_cell=defaultdict(lambda:{
        "animals":defaultdict(list),"original_steps":0,"matched_steps":0
    })
    for row in events:
        cell=row["cell"]
        if cell not in eligible:
            continue
        c=per_cell[cell]
        c["original_steps"]+=1
        climate=weather.get((cell[0],cell[1],row["utc_hour"].year),{}).get(row["utc_hour"])
        if climate is None:
            continue
        speed,from_bearing,radiation,temp=climate
        to_bearing=wind_flow_to(from_bearing)
        b,a=row["bearing"],row["sun_azimuth"]
        c["animals"][row["animal"]].append((
            wrap_cos_degrees(b,a),
            wrap_cos_degrees(b,to_bearing),
            wrap_cos_degrees(to_bearing,a),
            speed,radiation,temp
        ))
        c["matched_steps"]+=1
    response={}
    for cell,x in per_cell.items():
        means=[tuple(mean(v[i] for v in samples) for i in range(len(FIELDS)))
               for samples in x["animals"].values() if samples]
        if not means:
            response[cell]={"original_steps":x["original_steps"],"matched_steps":0,
                            "mean":None,"n_animals":0}
        else:
            response[cell]={"original_steps":x["original_steps"],
                            "matched_steps":x["matched_steps"],
                            "n_animals":len(means),
                            "mean":tuple(mean(v[i] for v in means) for i in range(len(FIELDS)))}
    return response


def join_one_pair(original_pair, original_taxa_cells, original_events, weather):
    aa,bb=original_pair["taxa"]
    common=set(original_taxa_cells[aa]) & set(original_taxa_cells[bb])
    if len(common)!=original_pair["shared_source_grid_month_solar_hour_cells"]:
        raise ValueError("Original matched GPS cells changed before weather inference")
    stat_a=matched_cell_stats(original_events[aa],weather,common)
    stat_b=matched_cell_stats(original_events[bb],weather,common)
    n_a=sum(x["original_steps"] for x in stat_a.values())
    n_b=sum(x["original_steps"] for x in stat_b.values())
    m_a=sum(x["matched_steps"] for x in stat_a.values())
    m_b=sum(x["matched_steps"] for x in stat_b.values())
    out={
        "taxa":[aa,bb],
        "registered_original_shared_cells":len(common),
        "original_GPS_steps_A":n_a,"original_GPS_steps_B":n_b,
        "ERA5_joined_steps_A":m_a,"ERA5_joined_steps_B":m_b,
        "fraction_steps_ERA5_qualified_A":m_a/n_a if n_a else 0,
        "fraction_steps_ERA5_qualified_B":m_b/n_b if n_b else 0,
        "baseline_no_weather_solar_pair_difference":original_pair["a_minus_b_solar_relative_bearing_cosine"],
        "status":"WEATHER_SOURCE_HOLD","environmental_differences":None
    }
    if min(out["fraction_steps_ERA5_qualified_A"],
           out["fraction_steps_ERA5_qualified_B"])<.90:
        out["hold_reason"]="Weather join below frozen 90% minimum original GPS step coverage"
        return out
    if any(x not in stat_a or x not in stat_b
           or stat_a[x]["mean"] is None or stat_b[x]["mean"] is None for x in common):
        out["hold_reason"]="At least one frozen shared original solar cell has no ERA5-matched steps"
        return out
    # A cell retains its original qualifying individual roster (>=3 animals).
    # If ERA5 drops some animal steps, output remains descriptive only.
    cellmeans_a=[stat_a[x]["mean"] for x in sorted(common)]
    cellmeans_b=[stat_b[x]["mean"] for x in sorted(common)]
    means_a=tuple(mean(x[i] for x in cellmeans_a) for i in range(len(FIELDS)))
    means_b=tuple(mean(x[i] for x in cellmeans_b) for i in range(len(FIELDS)))
    delta=tuple(means_a[i]-means_b[i] for i in range(len(FIELDS)))
    # Exact replay must hold when all original steps linked to weather.
    if m_a==n_a and m_b==n_b:
        if abs(delta[0]-original_pair["a_minus_b_solar_relative_bearing_cosine"])>1e-10:
            raise ValueError("Joined original GPS solar-only pair no longer replays")
        out["full_original_GPS_solar_difference_replayed"]=True
    else:
        out["full_original_GPS_solar_difference_replayed"]=False
    out["status"]="SOURCE_OBSERVED_ERA5_LINKED_DESCRIPTION"
    out["environmental_differences"]={
        "source_species_A_means":dict(zip(FIELDS,means_a)),
        "source_species_B_means":dict(zip(FIELDS,means_b)),
        "A_minus_B":dict(zip(FIELDS,delta)),
        "joint_solar_minus_windflow_heading_contrast_delta":delta[0]-delta[1],
        "shared_original_GPS_cell_weighting":"equal original qualifying cells, equal tagged animals inside each cell"
    }
    return out


def analyze_source(uuid,out):
    contract,source,pairs,prev=original_setup()
    file_source=source[uuid]
    src=file_source["original_file"]
    result={"source_package_uuid":uuid,"source_dois":file_source["original_dois"],
            "original_source_species_labels":file_source["original_species_labels"],
            "n_reference_supported_pairs":len(pairs[uuid]),
            "source_status":"SOURCE_HOLD","pair_results":[]}
    private=out/("private_source_"+uuid+".csv")
    try:
        files=[x for x in original_files(uuid) if x["bitstream_uuid"]==src["bitstream_uuid"]]
        if (len(files)!=1 or files[0]["checksum"]!=src["checksum"]
                or files[0]["bytes"]!=src["bytes"]):
            raise ValueError("Original provider source identity/checksum/bytes changed")
        original_check=checksum_and_download(files[0],private)
        result["original_provider_checksum_verified"]=original_check
        tracks,coverage,counts=load_source_taxa(
            private,src["filename"],file_source["original_species_labels"])
        result["original_observation_rows"]=counts["original_total_rows"]
        original_cells,replayed_pairs=preweather_replay(
            file_source,tracks,pairs[uuid],prev[uuid])
        result["original_frozen_solar_pairs_replayed"]=True
        wanted=defaultdict(set)
        for pair in replayed_pairs:
            if pair["status"]!="SUPPORTED_SOURCE_DESCRIPTIVE":
                continue
            aa,bb=pair["taxa"]
            joint=set(original_cells[aa]) & set(original_cells[bb])
            wanted[aa].update(joint);wanted[bb].update(joint)
        original_events=sampled_original_steps(tracks,wanted)
        result["source_original_steps_in_shared_solar_cells"]=sum(len(x) for x in original_events.values())
        frame=query_frame(original_events)
        result["modelled_ERA5_coarse_grid_year_requests"]=len(frame)
        result["source_original_solar_shared_cells"]=sum(len(x) for x in wanted.values())
        if len(frame)>contract["max_distinct_spatial_grid_utc_year_requests_per_source"]:
            raise ValueError("Weather original source query frame exceeds frozen per-source cap")
        weather,receipts=get_weather(
            frame,contract["max_distinct_spatial_grid_utc_year_requests_per_source"])
        result["source_weather_original_receipts_no_coordinates"]=receipts
        for pair in replayed_pairs:
            if pair["status"]!="SUPPORTED_SOURCE_DESCRIPTIVE":
                continue
            result["pair_results"].append(
                join_one_pair(pair,original_cells,original_events,weather))
        result["source_status"]="SOURCE_ENVIRONMENTAL_DESCRIPTION_COMPLETED"
    except Exception as exc:
        # Provider URLs and individual source locations never appear in error report.
        result["source_status"]="SOURCE_HOLD"
        result["failure_type"]=type(exc).__name__
        result["failure_step"]="before_OR_during_original_environment_join"
        result["pair_results"]=[
            {"taxa":p["taxa"],"status":"SOURCE_HOLD",
             "baseline_no_weather_solar_pair_difference":p["a_minus_b_solar_relative_bearing_cosine"]}
            for p in pairs[uuid]]
    finally:
        private.unlink(missing_ok=True)
    return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--source-index",required=True,type=int,choices=(0,1))
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    contract,source,pairs,prev=original_setup()
    uuid=contract["exact_studies"][args.source_index]["uuid"]
    result=analyze_source(uuid,args.out)
    output={
       "version":"original-shared-cell-solar-wind-irradiance-v0",
       "source_index":args.source_index,"n_original_studies":1,
       "original_study_result":result,
       "qualified_environment_pair_results":sum(p["status"]=="SOURCE_OBSERVED_ERA5_LINKED_DESCRIPTION"
                                                 for p in result["pair_results"]),
       "source_claim_limit":"Coarse ERA5 100m wind and shortwave over source-matched original GPS, exploratory after prior solar effects. No direct causal solar/wind response, independent biome test or actual animal sunlight exposure."
    }
    (args.out/("solar_wind_original_source_"+str(args.source_index)+".json")).write_text(
        json.dumps(output,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("SOLAR_WIND_ORIGINAL_SOURCE_RESULT "+
          json.dumps(output,ensure_ascii=False,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
