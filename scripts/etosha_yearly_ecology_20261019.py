"""Etosha two-species year-stratified ecological contrasts and regional hydroclimate.

Separate 2009 and 2010 source-supported Southern summer-solstice cycles,
on identical time-only hourly GPS sampling. Reproduce the frozen pooled
2009+2010 GPS results before opening year-specific outcomes. No raw tags,
coordinates or exact matched animal dates exported.
"""
import argparse, json
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import mean

from scripts.movebank_native_ecology_20261019 import HERE, original_files, checksum_and_download, solar_period
from scripts.movebank_southern_solar_mammal_20261019 import (
    southern_solar_cycle, matched_pairs, safe_unzip_data_csv
)
from scripts import movebank_southern_solar_mammal_20261019 as south
from scripts.movebank_elephant_hourly_20261019 import thinned_loader
from scripts.movebank_solar_movement_20261019 import valid_interval
from scripts.movebank_regional_climate_link_20261019 import read_weather
from scripts.etosha_shared_climate_20261019 import join_region_climate

CONTRACT = HERE / "research/ETOSHA_YEAR_STRATIFIED_ECOLOGY_V0_20261019.json"
SOUTH = HERE / "research/MOVEBANK_SOUTHERN_SOLAR_MOVEMENT_V0_20261019.json"
YEARS = (2009, 2010)

def choose_solar_cycles(tracks, cycles):
    included={}
    for animal, rows in tracks.items():
        fixes=[]
        for t,lat,lon in rows:
            d,_=solar_period(t,lat,lon)
            cy,_=southern_solar_cycle(d)
            if cy in cycles:
                fixes.append((t,lat,lon))
        if fixes:
            included[animal]=fixes
    return included

def read_gps_effect_on_tracks(tracks, source_rows, invalid_rows):
    """Call UNMODIFIED previous ecological endpoint on the supplied fixed source roster."""
    old=south.load_events
    def supplied_loader(_):
        return {key:list(fixes) for key,fixes in tracks.items()},source_rows,invalid_rows
    try:
        south.load_events=supplied_loader
        return south.analyze_south(Path("provider_checksum_verified_source.csv"))
    finally:
        south.load_events=old

def observation_date_roster(tracks):
    """Only observed GPS opportunities determine matched seasonal dates."""
    raw=defaultdict(lambda:{"day":0,"night":0,"lat_total":0.0,"n":0})
    for animal,values in tracks.items():
        ordered=sorted(values,key=lambda r:r[0])
        for a,b in zip(ordered,ordered[1:]):
            interval=valid_interval(a[0],a[1],a[2],b[0],b[1],b[2])
            if interval is None:continue
            d,part,_speed,_hours,lat=interval
            if lat>=0:continue
            state=raw[(animal,d)]
            state[part]+=1;state["lat_total"]+=lat;state["n"]+=1
    by_cycle=defaultdict(dict)
    for (animal,d),counts in raw.items():
        if counts["day"]<3 or counts["night"]<3:continue
        cy,branch=southern_solar_cycle(d)
        if cy not in YEARS:continue
        by_cycle[(animal,cy)][d]={
            "lat":counts["lat_total"]/counts["n"],
            "branch":branch,
            "n_day":counts["day"],
            "n_night":counts["night"]
        }
    out={y:{} for y in YEARS}
    for (animal,cy),days in by_cycle.items():
        if {x["branch"] for x in days.values()} != {"rising","falling"}:continue
        pairs=matched_pairs(days)
        if len(pairs)>=10:
            out[cy][animal]=[pairs]
    return out

def calendar_coverage(animals):
    pairs={pair for cycles in animals.values() for batch in cycles for pair in batch}
    return {
        "unique_qualified_astronomical_date_pairs":len(pairs),
        "all_unique_rising_dates":{a for a,b in pairs},
        "all_unique_falling_dates":{b for a,b in pairs},
        "pair_set":pairs,
        "count_total_individual_matched_pairs":sum(len(batch) for cycles in animals.values() for batch in cycles)
    }

def shared_date_coverage(a,b):
    x,y=calendar_coverage(a),calendar_coverage(b)
    return {
       "unique_qualified_pairs_elephant":x["unique_qualified_astronomical_date_pairs"],
       "unique_qualified_pairs_jackal":y["unique_qualified_astronomical_date_pairs"],
       "identical_unique_date_pairs_supported_in_both_sources":len(x["pair_set"] & y["pair_set"]),
       "individual_matched_pairs_elephant":x["count_total_individual_matched_pairs"],
       "individual_matched_pairs_jackal":y["count_total_individual_matched_pairs"],
       "common_unique_rising_dates":len(x["all_unique_rising_dates"] & y["all_unique_rising_dates"]),
       "common_unique_falling_dates":len(x["all_unique_falling_dates"] & y["all_unique_falling_dates"])
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    contract=json.loads(CONTRACT.read_text())
    if contract["version"]!="etosha-independent-solar-year-ecology-v0" or contract["fixed_admitted_solar_years"]!=list(YEARS):
        raise ValueError("Unfrozen year-stratified route")
    sources={x["label"]:x for x in json.loads(SOUTH.read_text())["sources"]}
    climate_reference={"latitude":-19.0,"longitude":16.0}
    all_sources=[]
    private_by_year={}
    for label in ("etosha_elephant","etosha_jackal"):
        src=sources[label]
        native=args.out/(label+".native")
        csv=args.out/(label+".csv")
        record={"source":label,"taxon":src["taxon"],"doi":src["doi"],
                "year_rule":"southern_december_summer_2009_and_2010"}
        try:
            files=[f for f in original_files(src["package_uuid"]) if f["bitstream_uuid"]==src["provider_original_bitstream_uuid"]]
            if len(files)!=1 or files[0]["checksum"]["value"].lower()!=src["provider_original_md5"].lower():
                raise ValueError("Original provider-MD5 source mismatch")
            record["provider_original_md5_checked"]=checksum_and_download(files[0],native)
            if src["provider_filename"].endswith(".zip"):
                safe_unzip_data_csv(native,csv)
            else:
                native.replace(csv)
            tracks,source_rows,invalid_rows=thinned_loader(csv)
            selected=choose_solar_cycles(tracks,set(YEARS))
            before=read_gps_effect_on_tracks(selected,source_rows,invalid_rows)
            target=contract["frozen_aggregate_replay"][label]
            if before.get("effect_status")!="exploratory_population_description" or abs(
                before["effect"]["mean_falling_minus_rising_log1p_night_over_day_kmh"]-target)>1e-12:
                raise ValueError("Previously verified 2009+2010 GPS effect failed exact replay")
            record["frozen_common_year_effect_reproduced"]=True
            roster=observation_date_roster(selected)
            private_by_year[label]=roster
            record["year_results"]={}
            for year in YEARS:
                cohort=choose_solar_cycles(selected,{year})
                effect=read_gps_effect_on_tracks(cohort,source_rows,invalid_rows)
                record["year_results"][str(year)]={
                    "source_year_independent_animals":effect.get("qualifying_distinct_individuals",0),
                    "matched_animal_date_pairs":effect.get("one_to_one_matched_day_pairs",0),
                    "status":effect.get("effect_status"),
                    "within_source_effect":effect.get("effect")
                }
                counts=calendar_coverage(roster[year])
                if counts["count_total_individual_matched_pairs"]!=effect.get("one_to_one_matched_day_pairs",0):
                    raise ValueError("Outcome-blind calendar roster does not reproduce source-matched pair count")
            record["original_source_rows"]=source_rows
            record["hourly_fix_observations"]=sum(len(x) for x in tracks.values())
        except Exception as e:
            record.update(status="source_hold",error=f"{type(e).__name__}: {e}")
        finally:
            native.unlink(missing_ok=True);csv.unlink(missing_ok=True)
        all_sources.append(record)
    if len(private_by_year)!=2:
        report={"status":"source_hold","source_groups":all_sources}
    else:
        dates=[d for by_year in private_by_year.values() for cohort in by_year.values()
               for batches in cohort.values() for pairs in batches for a,b in pairs for d in (a,b)]
        weather,receipts=read_weather(climate_reference,min(dates),max(dates))
        years=[]
        for year in YEARS:
            species={}
            for label in ("etosha_elephant","etosha_jackal"):
                roster=private_by_year[label][year]
                species[label]=join_region_climate(roster,weather)
            years.append({"southern_solar_year":year,
                          "shared_calendar_support":shared_date_coverage(
                              private_by_year["etosha_elephant"][year],
                              private_by_year["etosha_jackal"][year]),
                          "regional_era5_comparison":species})
        report={"status":"completed_comparative_observational_ecology",
                "scope":"Post-outcome year-stratified wildlife displacement and shared-grid regional weather, not causal species effect",
                "source_groups":all_sources,"yearly_environment_and_calendar_overlap":years,
                "environment_reference":"Etosha 19°S 16°E, same ERA5 source grid for both mammals",
                "era5_source_receipts":receipts}
    (args.out/"etosha_year_by_year_ecology.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("ETOSHA_YEARLY_ECOLOGY "+json.dumps(report,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
