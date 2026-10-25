"""Ecological calendar coupling across original Utah and Wyoming ungulate studies.

Why does a nearly identical marginal mule deer q~L slope in two public original
GPS archives yield opposing climate-adjusted daylength estimates? Algebraically
decompose same-sample observational associations, WITHOUT claiming causation.

No animal, GPS, cell identifier, exact date, or individual model row exported.
"""
import argparse,json,math
from collections import defaultdict
from pathlib import Path
from statistics import mean

from scripts.movebank_native_ecology_20261019 import HERE,original_files,checksum_and_download
from scripts.movebank_utah_four_taxa_solar_20261019 import (
    CONTRACT as UTAH_SOURCE,extract_time_only_original_source
)
from scripts.movebank_wyoming_two_ungulates_20261022 import (
    CONTRACT as WYOMING_SOURCE,streaming_time_selected_csv
)
from scripts.movebank_utah_diel_photoperiod_20261019 import one_taxon
from scripts.movebank_wyoming_individual_era5_20261023 import source_admitted_daily
from scripts.movebank_wyoming_daily_climate_20261023 import daily_source_era5,climate_at_gps_day
from scripts.movebank_utah_calendar_condition_20261022 import partial_slope
from scripts.movebank_utah_shared_spatial_20261019 import cluster_interval

CONTRACT=HERE/"research/ODSP_TWO_STUDY_ECOLOGICAL_CALENDAR_COUPLING_V0_20261025.json"
UTAH_DAILY=HERE/"research/UTAH_FOUR_TAXON_DAILY_CLIMATE_DAYLIGHT_V1_20261023.json"
WYOMING_DAILY=HERE/"research/WYOMING_DAILY_ERA5_DAYLIGHT_V1_20261023.json"

def simple_slope(x,y):
    if len(x)!=len(y) or len(x)<2:raise ValueError("Invalid paired observations")
    xm=mean(x);ym=mean(y)
    den=sum((a-xm)**2 for a in x)
    if den<=1e-12:return None
    return sum((a-xm)*(b-ym) for a,b in zip(x,y))/den

def year_decomposition(rows):
    """q~L omitted-variable identity on SAME original GPS and ERA5 matched days."""
    if len(rows)<15 or max(v[2] for v in rows)-min(v[2] for v in rows)<.5:
        return None
    def fit(predictor,controls,sd):
        return partial_slope(rows,predictor,controls,
                             minimum_n=15,residual_sd=sd,minimum_daylength_sd=.2)
    base=fit(2,[],.1)
    direct=fit(2,[0,1],.1)
    t_coef=fit(0,[2,1],.5)
    w_coef=fit(1,[2,0],.1)
    if any(v is None for v in (base,direct,t_coef,w_coef)):
        return None
    l=[v[2] for v in rows]
    gamma_t=simple_slope(l,[v[0] for v in rows])
    gamma_w=simple_slope(l,[v[1] for v in rows])
    if gamma_t is None or gamma_w is None:return None
    thermal=t_coef*gamma_t
    hydric=w_coef*gamma_w
    reconstruction=direct+thermal+hydric
    error=abs(reconstruction-base)
    if error>1e-8:raise ValueError("Algebraic ecological calendar decomposition failed")
    return {
      "raw_L_association_on_exact_joint_sample":base,
      "conditional_L_association":direct,
      "seasonal_Tmax_calendar_component":thermal,
      "seasonal_PminusET0_calendar_component":hydric,
      "original_Tmax_per_hour_daylight":gamma_t,
      "original_PminusET0_100mm_per_hour_daylight":gamma_w,
      "conditional_Tmax_coefficient_per_C":t_coef,
      "conditional_PminusET0_coefficient_per100mm":w_coef,
      "source_days":len(rows),
      "identity_error":error
    }

def group_by_animal_year(admitted,weather):
    """Identical previous date-level climate and GPS assembly, no feature engineering."""
    grouped=defaultdict(list)
    counts={"original_source_animal_years":len(admitted),
            "source_days_missing_complete_ERA5":0,
            "source_animal_years_not_estimable":0,
            "source_weather_complete_days":0,
            "same_source_year_decompositions":0}
    for animal,year,days in admitted:
        obs=[]
        for d,light,q,cell,ym in days:
            climate=climate_at_gps_day(weather.get(cell,{}),d)
            if climate is None:
                counts["source_days_missing_complete_ERA5"]+=1;continue
            tmean,tmax,water=climate
            obs.append((tmax,water,light,q))
            counts["source_weather_complete_days"]+=1
        result=year_decomposition(obs)
        if result is None:
            counts["source_animal_years_not_estimable"]+=1
            continue
        grouped[animal].append(result)
        counts["same_source_year_decompositions"]+=1
    return grouped,counts

def summarize(grouped,counts):
    keys=["raw_L_association_on_exact_joint_sample",
          "conditional_L_association",
          "seasonal_Tmax_calendar_component",
          "seasonal_PminusET0_calendar_component",
          "original_Tmax_per_hour_daylight",
          "original_PminusET0_100mm_per_hour_daylight",
          "conditional_Tmax_coefficient_per_C",
          "conditional_PminusET0_coefficient_per100mm"]
    per_animal=[{key:mean(x[key] for x in years) for key in keys} for years in grouped.values()]
    statistics={}
    for key in keys:
        data=[v[key] for v in per_animal]
        statistics[key]={
          "equal_animal_mean":mean(data) if len(data)>=5 else None,
          "animal_bootstrap_95":cluster_interval(data) if len(data)>=5 else None,
          "positive_source_animals":sum(x>0 for x in data),
          "negative_source_animals":sum(x<0 for x in data)}
    out={**counts,"estimable_source_individuals":len(per_animal),
         "source_equal_individual_associations":statistics}
    if per_animal:
        raw=statistics["raw_L_association_on_exact_joint_sample"]["equal_animal_mean"]
        cond=statistics["conditional_L_association"]["equal_animal_mean"]
        thermal=statistics["seasonal_Tmax_calendar_component"]["equal_animal_mean"]
        water=statistics["seasonal_PminusET0_calendar_component"]["equal_animal_mean"]
        if None not in (raw,cond,thermal,water):
            out["group_omitted_variable_identity_max_abs_error"]=abs(raw-(cond+thermal+water))
            if out["group_omitted_variable_identity_max_abs_error"]>1e-8:
                raise ValueError("Averaged animal identity not preserved")
    return out

def original_source(source,config):
    if source=="utah":
        p=json.loads(UTAH_SOURCE.read_text())["source"]
        d=json.loads(UTAH_DAILY.read_text())
        checks={x["taxon"]:x for x in d["source_reference_results"]}
        return p,checks
    p=json.loads(WYOMING_SOURCE.read_text())["source"]
    d=json.loads(WYOMING_DAILY.read_text())
    checks=d["original_effect_replay"]
    return p,checks

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",choices=("utah","wyoming"),required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    freeze=json.loads(CONTRACT.read_text())
    if freeze["version"]!="odsp-two-study-solar-ecological-calendar-coupling-v0":
        raise ValueError("Unfrozen observational coupling route")
    f=freeze["sources"][args.source]
    src,prior=original_source(args.source,f)
    taxa=f["taxa"]
    if args.source=="utah":
        known=src["catalog_taxa"]
        hashkey="original_md5"; packagekey="package_uuid"; streamkey="original_bitstream_uuid"
        byteskey="original_bytes"
    else:
        known=src["published_species"]
        hashkey="original_md5"; packagekey="package_uuid"; streamkey="original_bitstream_uuid"
        byteskey="original_bytes"
    if set(known)!=set(taxa) or src[hashkey]!=f["original_md5"]:
        raise ValueError("Wrong fixed source taxa or original MD5")
    result={"cohort":args.source,"source_doi":f["doi"],"taxa":[],
            "original_GPS_effects_replayed":False,"prior_adjusted_L_replayed":False,
            "environment_stage":"ERA5 historical 1degree cells and past 30d water index, unchanged source observations"}
    path=args.out/"original_source.bin"
    try:
        fs=[x for x in original_files(src[packagekey]) if x["bitstream_uuid"]==src[streamkey]]
        if len(fs)!=1 or fs[0]["checksum"]["value"].lower()!=src[hashkey].lower() or fs[0]["bytes"]!=src[byteskey]:
            raise ValueError("Provider ORIGINAL UUID, MD5 or source byte count changed")
        result["original_MD5_verified"]=checksum_and_download(fs[0],path)
        if args.source=="utah":
            groups,source_counts,unclassified=extract_time_only_original_source(path,taxa)
        else:
            groups,source_counts,unclassified=streaming_time_selected_csv(path,taxa)
        result["unclassified_taxon_source_rows"]=unclassified
        by_taxon={}
        for taxon in taxa:
            original,_=one_taxon(taxon,groups[taxon])
            q=original["day_night_speed_contrast"]
            l=original["daylength_association"]
            if q is None or l is None:raise ValueError("Originally admitted source diel/daylight effect unavailable")
            old=prior[taxon]
            if args.source=="utah":
                expect=(old["qualified_q_animals"],old["group_q"],old["qualified_daylight_animals"],old["daylight_slope"])
            else:
                expect=(old["n"],old["q"],old["slope_n"],old["slope"])
            if (q["n_individuals"]!=expect[0] or abs(q["mean"]-expect[1])>1e-12 or
                l["n_individuals"]!=expect[2] or abs(l["mean"]-expect[3])>1e-12):
                raise ValueError("Original public GPS day/night or daylength effect failed exact replay")
            by_taxon[taxon]=source_admitted_daily(groups[taxon])
            groups[taxon].clear()
            result["taxa"].append({"taxon":taxon,
                "original_q_effect":q["mean"],"original_raw_L_mean":l["mean"],
                "original_GPS_qualifying_animals":q["n_individuals"],
                "original_daylight_qualifying_animals":l["n_individuals"]})
        result["original_GPS_effects_replayed"]=True
        framed=defaultdict(set)
        for taxa_days in by_taxon.values():
            for animal,year,days in taxa_days:
                for d,L,q,cell,ym in days:
                    framed[cell].add(d)
        result["source_climate_grid_count"]=len(framed)
        if len(framed)>f["maximum_original_weather_cells"]:
            raise ValueError("Original source weather frame unexpectedly too large. No outcome-dependent cell exclusions.")
        weather={};receipts=[];held=0
        for cell,dates in sorted(framed.items()):
            try:
                values,receipt=daily_source_era5(cell,dates)
                weather[cell]=values
                receipts.append(receipt["source_response_sha256"])
            except Exception as e:
                held+=1
                receipts.append({"source_hold":type(e).__name__})
        result["original_ERA5_source_SHA256s"]=receipts
        result["weather_source_holds"]=held
        for item in result["taxa"]:
            animal_data,counts=group_by_animal_year(by_taxon[item["taxon"]],weather)
            out=summarize(animal_data,counts)
            item.update(out)
            prior_mean=f["known_previous_joint_L"][item["taxon"]]
            original_sample_values={}
            # Recheck the known prior joint coefficient on the precise previous
            # joint-eligible date set, even if the full decomp has more gates.
            joint_animals=defaultdict(list)
            for animal,year,days in by_taxon[item["taxon"]]:
                obs=[]
                for d,L,q,cell,ym in days:
                    v=climate_at_gps_day(weather.get(cell,{}),d)
                    if v is None:continue
                    obs.append((v[1],v[2],L,q))
                if len(obs)<10 or max((x[2] for x in obs),default=-99)-min((x[2] for x in obs),default=99)<.5:
                    continue
                fitted=partial_slope(obs,2,[0,1],minimum_n=15,residual_sd=.1,minimum_daylength_sd=.2)
                if fitted is not None:joint_animals[animal].append(fitted)
            vals=[mean(z) for z in joint_animals.values()]
            got=mean(vals) if len(vals)>=5 else None
            if got is None or abs(got-prior_mean)>1e-10 or len(vals)!=f["known_qualified_joint_animals"][item["taxon"]]:
                raise ValueError("Previously published original source climate-adjusted daylight coefficient did not replay: "+json.dumps({"taxon":item["taxon"],"expected":prior_mean,"actual":got,"expected_n":f["known_qualified_joint_animals"][item["taxon"]],"actual_n":len(vals)}))
            item["prior_joint_daylight_replayed"]=got
            item["prior_joint_admitted_animals_replayed"]=len(vals)
            by_taxon[item["taxon"]].clear()
            print("SOURCE_ECOLOGICAL_CALENDAR_DECOMPOSITION "+json.dumps(item,sort_keys=True),flush=True)
        result["prior_adjusted_L_replayed"]=True
        result["status"]="observational_ecological_calendar_decomposition_completed"
    except Exception as e:
        result.update(status="SOURCE_HOLD",error=f"{type(e).__name__}: {e}")
    finally:path.unlink(missing_ok=True)
    (args.out/(args.source+"_calendar_decomposition.json")).write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("ECOLOGICAL_CALENDAR_COUPLING_SUMMARY "+json.dumps({
        "source":args.source,"status":result["status"],"source_GPS_replayed":result["original_GPS_effects_replayed"],
        "previous_climate_model_replayed":result["prior_adjusted_L_replayed"],
        "taxa":len(result["taxa"]),"original_climate_grids":result.get("source_climate_grid_count"),
        "weather_holds":result.get("weather_source_holds"),"error":result.get("error")},sort_keys=True))
    if result["status"]=="SOURCE_HOLD":raise SystemExit(2)
if __name__=="__main__":main()
