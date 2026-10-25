"""Utah four-taxon original GPS × daily ERA5 solar-season ecology.

Same predeclared daily climate adjustment as the independent Wyoming mammal
source; all FOUR Utah source taxa and all original source observation dates
are retained. Original GPS source effects replayed before new weather data.
No animal coordinates, exact dates, individuals or grid IDs in public outputs.
"""
import argparse,json
from collections import defaultdict
from pathlib import Path
from scripts.movebank_native_ecology_20261019 import HERE,original_files,checksum_and_download
from scripts.movebank_utah_four_taxa_solar_20261019 import (
    CONTRACT as ORIGINAL_UTAH,extract_time_only_original_source
)
from scripts.movebank_utah_diel_photoperiod_20261019 import one_taxon
from scripts.movebank_wyoming_individual_era5_20261023 import (
    source_admitted_daily
)
from scripts.movebank_wyoming_daily_climate_20261023 import (
    daily_source_era5,adjusted_daily_effects
)

CONTRACT=HERE/"research/UTAH_FOUR_TAXON_DAILY_CLIMATE_DAYLIGHT_V1_20261023.json"

def collect_animal_observed_grids(source_admitted):
    frame=defaultdict(set)
    for _taxon,rows in source_admitted.items():
        for animal,year,days in rows:
            for d,light,q,cell,ym in days:
                frame[cell].add(d)
    return frame

def original_replay(taxon,animals,reference):
    observed,_=one_taxon(taxon,animals)
    q=observed["day_night_speed_contrast"]
    s=observed["daylength_association"]
    if q is None or s is None:
        raise ValueError("Previously supported source taxon GPS endpoint is unavailable")
    if q["n_individuals"]!=reference["qualified_q_animals"] or abs(q["mean"]-reference["group_q"])>1e-12:
        raise ValueError("Frozen public original taxon group q failed replay")
    if s["n_individuals"]!=reference["qualified_daylight_animals"] or abs(s["mean"]-reference["daylight_slope"])>1e-12:
        raise ValueError("Frozen public original taxon group sunlight slope failed replay")
    return {"baseline_q_replayed":q["mean"],"baseline_solar_slope_replayed":s["mean"],
        "baseline_qualified_q_animals":q["n_individuals"],
        "baseline_qualified_solar_animals":s["n_individuals"]}

def main():
    p=argparse.ArgumentParser();p.add_argument("--out",required=True,type=Path)
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    spec=json.loads(CONTRACT.read_text())
    if spec["version"]!="utah-all-four-daily-original-gps-era5-daylight-v1":
        raise ValueError("Unfrozen Utah public source/day-level original climate ecology route")
    src=json.loads(ORIGINAL_UTAH.read_text())["source"]
    frame={r["taxon"]:r for r in spec["source_reference_results"]}
    if set(frame)!=set(src["catalog_taxa"]):
        raise ValueError("Registered original source four-taxon cohort mismatch")
    outcome={"study":"Utah UDWR original four-ungulate same original daily ERA5/sunlight source",
             "source_doi":src["doi"],"source_GPS_results_replayed":False,
             "weather_source_grids":[],"source_taxa":[]}
    z=args.out/"source_original_utah.zip"
    try:
        files=[x for x in original_files(src["package_uuid"]) if x["bitstream_uuid"]==src["original_bitstream_uuid"]]
        if len(files)!=1 or files[0]["checksum"]["value"].lower()!=src["original_md5"].lower() or files[0]["bytes"]!=src["original_bytes"]:
            raise ValueError("Original Utah public source MD5/bitstream/size mismatch")
        outcome["source_original_MD5_verified"]=checksum_and_download(files[0],z)
        taxa,counts,unknown=extract_time_only_original_source(z,src["catalog_taxa"])
        by_taxon={}
        for taxon in src["catalog_taxa"]:
            replay=original_replay(taxon,taxa[taxon],frame[taxon])
            admit=source_admitted_daily(taxa[taxon])
            replay["taxon"]=taxon
            replay["source_admitted_individual_years"]=len(admit)
            outcome["source_taxa"].append(replay)
            by_taxon[taxon]=admit
            taxa[taxon].clear()
        outcome["source_GPS_results_replayed"]=True
        geogrids=collect_animal_observed_grids(by_taxon)
        outcome["source_admitted_one_degree_ERA5_grids"]=len(geogrids)
        if len(geogrids)>160:
            raise ValueError("Original source observed too many geographic ERA5 cells; source HOLD without outcome-dependent exclusions")
        weather={};receipts=[];holds=0
        for cell,dates in sorted(geogrids.items()):
            try:
                records,receipt=daily_source_era5(cell,dates)
                weather[cell]=records
                receipts.append(receipt)
            except Exception as e:
                holds+=1
                receipts.append({"status":"ERA5_SOURCE_HOLD","error_type":type(e).__name__})
        outcome["source_ERA5_receipts"]=receipts
        outcome["weather_source_grid_holds"]=holds
        for item in outcome["source_taxa"]:
            s=adjusted_daily_effects(by_taxon[item["taxon"]],weather)
            item.update(s)
            print("UTAH_SOURCE_ORIGINAL_DAILY_CLIMATE_DAYLIGHT "+json.dumps(item,sort_keys=True),flush=True)
            by_taxon[item["taxon"]].clear()
        outcome["status"]="four_taxon_original_daily_climate_and_sunlight_ecology_completed"
    except Exception as ex:
        outcome.update(status="SOURCE_HOLD",error=f"{type(ex).__name__}: {ex}")
    finally:z.unlink(missing_ok=True)
    (args.out/"utah_four_taxa_daily_climate_daylight.json").write_text(json.dumps(outcome,indent=2)+"\n")
    print("UTAH_ORIGINAL_FOUR_TAXON_DAILY_CLIMATE_SUMMARY "+json.dumps({
        "status":outcome["status"],"original_GPS_replayed":outcome["source_GPS_results_replayed"],
        "ERA5_grids":outcome.get("source_admitted_one_degree_ERA5_grids"),
        "ERA5_source_holds":outcome.get("weather_source_grid_holds"),
        "taxa_processed":len(outcome["source_taxa"])
    },sort_keys=True))
if __name__=="__main__":main()
