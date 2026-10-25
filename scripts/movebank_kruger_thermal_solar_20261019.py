"""Within-elephant same-solar-daylength thermal gradient and GPS diel movement contrasts.

Source article already established elephant collar temperature/movement association;
this route specifically estimates individual-centered paired-daylength difference-of-
differences. Sensor collar T is a RELATIVE microthermal indicator, NOT body temperature.
No event, individual, coordinate, date or raw sensor values are exported.
"""
import argparse,csv,json,math,random
from collections import defaultdict
from pathlib import Path
from statistics import mean,median,pstdev
from scripts.movebank_native_ecology_20261019 import HERE,original_files,checksum_and_download,parse_time
from scripts.movebank_elephant_hourly_20261019 import choose_one_per_utc_hour, thinned_loader
from scripts.movebank_solar_movement_20261019 import valid_interval
from scripts.movebank_southern_solar_mammal_20261019 import southern_solar_cycle,matched_pairs
from scripts import movebank_southern_solar_mammal_20261019 as south

CONTRACT=HERE/"research/MOVEBANK_KRUGER_THERMAL_DIEL_V0_20261019.json"
SOURCE=HERE/"research/MOVEBANK_KRUGER_ELEPHANT_INDEPENDENT_V0_20261019.json"

def choose_hour_with_temperature(fixes):
    """Select only on UTC timestamps; preserve original temperature of chosen source fix."""
    pick={}
    for row in fixes:
        t=row[0];hour=t.replace(minute=0,second=0,microsecond=0)
        secs=(t-hour).total_seconds()
        if hour not in pick or secs<pick[hour][0]:
            pick[hour]=(secs,row)
    return [v[1] for _,v in sorted(pick.items())]

def load_raw_thermal(path):
    tracks=defaultdict(list)
    counted={"source_rows":0,"invalid_gps_rows":0,"temperature_missing_or_non_numeric":0,"temperature_outside_fixed_range":0,"temperature_admitted_source_fixes":0}
    with path.open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        col={str(k).strip().lower():k for k in (rd.fieldnames or [])}
        required=("timestamp","individual-local-identifier","location-lat","location-long","external-temperature")
        if not all(x in col for x in required):
            raise ValueError("Source thermal/GPS columns mismatch: "+str(sorted(col)))
        for row in rd:
            counted["source_rows"]+=1
            t=parse_time(row[col["timestamp"]]);ind=(row[col["individual-local-identifier"]] or "").strip()
            try:lat=float(row[col["location-lat"]]);lon=float(row[col["location-long"]])
            except (ValueError,TypeError):lat=lon=float("nan")
            if t is None or not ind or not(math.isfinite(lat) and math.isfinite(lon) and abs(lat)<=90 and abs(lon)<=180):
                counted["invalid_gps_rows"]+=1;continue
            val=row.get(col["external-temperature"],"")
            try:temp=float(val)
            except (ValueError,TypeError):temp=float("nan")
            if not math.isfinite(temp):
                temp=None;counted["temperature_missing_or_non_numeric"]+=1
            elif not(-40<=temp<=90):
                temp=None;counted["temperature_outside_fixed_range"]+=1
            else:counted["temperature_admitted_source_fixes"]+=1
            tracks[ind].append((t,lat,lon,temp))
    return tracks,counted

def within_year_slope(pairs):
    """Pair values x,y; return finite OLS slope and paired means."""
    if len(pairs)<10:return None
    xs=[z[0] for z in pairs];ys=[z[1] for z in pairs]
    xbar=mean(xs);ybar=mean(ys)
    var=sum((x-xbar)**2 for x in xs)/len(xs)
    if var<0.01:return None  # prespecified sd(x) < 0.1°C => no identifiable slope
    slope=sum((x-xbar)*(y-ybar) for x,y in zip(xs,ys))/sum((x-xbar)**2 for x in xs)
    return slope,xbar,ybar,len(pairs)

def source_solar_pairs(tracks):
    """GPS-date selection matches source-locked Southern v0 independently of T."""
    daily=defaultdict(lambda:{"day":[],"night":[],"day_t":[],"night_t":[],"lat":[]})
    start_t_missing=0;used=0
    for ind,fixes in tracks.items():
        selected=choose_hour_with_temperature(fixes)
        for a,b in zip(selected,selected[1:]):
            segment=valid_interval(a[0],a[1],a[2],b[0],b[1],b[2])
            if segment is None:continue
            d,part,speed,h,lat=segment
            if lat>=0:continue
            used+=1
            s=daily[(ind,d)]
            s[part].append(speed);s["lat"].append(lat)
            if a[3] is not None:s[part+"_t"].append(a[3])
            else:start_t_missing+=1
    by_year=defaultdict(dict)
    for (ind,d),v in daily.items():
        if len(v["day"])<3 or len(v["night"])<3:continue
        y,branch=southern_solar_cycle(d)
        if y is None:continue
        by_year[(ind,y)][d]={
            "branch":branch,"lat":mean(v["lat"]),
            "n_day":len(v["day"]),"n_night":len(v["night"]),
            "speed_day":median(v["day"]),"speed_night":median(v["night"]),
            "thermal_day":median(v["day_t"]) if len(v["day_t"])>=2 else None,
            "thermal_night":median(v["night_t"]) if len(v["night_t"])>=2 else None
        }
    by_elephant=defaultdict(list)
    movement_qualified_pairs=0;thermal_qualified_pairs=0;not_complete=0
    for (animal,cycle),days in by_year.items():
        if {v["branch"] for v in days.values()}!={"rising","falling"}:continue
        pairs=matched_pairs(days)
        if len(pairs)<10:continue
        movement_qualified_pairs+=len(pairs)
        records=[]
        for a,b in pairs:
            rising,falling=days[a],days[b]
            if any(v is None for v in (rising["thermal_day"],rising["thermal_night"],falling["thermal_day"],falling["thermal_night"])):
                not_complete+=1;continue
            tdiff=(falling["thermal_day"]-falling["thermal_night"])-(rising["thermal_day"]-rising["thermal_night"])
            mday=math.log1p(falling["speed_day"])-math.log1p(rising["speed_day"])
            mnight=math.log1p(falling["speed_night"])-math.log1p(rising["speed_night"])
            records.append((tdiff,mnight-mday,falling["thermal_day"]-rising["thermal_day"],falling["thermal_night"]-rising["thermal_night"]))
            thermal_qualified_pairs+=1
        slope=within_year_slope([(x[0],x[1]) for x in records])
        if slope is None:continue
        by_elephant[animal].append({
            "slope":slope[0],"delta_thermal_day_vs_night":slope[1],
            "delta_relative_gps_movement":slope[2],
            "delta_thermal_day":mean(x[2] for x in records),
            "delta_thermal_night":mean(x[3] for x in records),
            "eligible_pairs":slope[3]
        })
    stats={"gps_valid_intervals_in_solar_day_or_night":used,
           "gps_valid_interval_start_temperature_missing":start_t_missing,
           "movement_eligible_source_date_pairs":movement_qualified_pairs,
           "sensor_temperature_complete_source_date_pairs":thermal_qualified_pairs,
           "sensor_incomplete_date_pairs":not_complete,
           "source_individuals_with_identifiable_within_year_thermal_slope":len(by_elephant),
           "qualified_thermal_individual_solar_years":sum(len(x) for x in by_elephant.values())}
    return by_elephant,stats

def estimate(individuals):
    if len(individuals)<5:
        return {"status":"temperature_slope_insufficient_independent_animals","source_individuals":len(individuals)}
    values=[]
    for yearly in individuals.values():
        values.append({key:mean(y[key] for y in yearly)
                       for key in ("slope","delta_thermal_day_vs_night","delta_relative_gps_movement","delta_thermal_day","delta_thermal_night")})
    slopes=[x["slope"] for x in values]
    rng=random.Random(20261019)
    sims=sorted(mean(slopes[rng.randrange(len(slopes))] for _ in slopes) for _ in range(2000))
    return {
        "status":"within_individual_thermal_gradient_association",
        "n_independent_elephants":len(values),
        "mean_within_elephant_year_centered_slope_log1p_relative_kmh_per_C":mean(slopes),
        "individual_bootstrap_95_percentile_interval":[sims[49],sims[1949]],
        "positive_individual_slope_count":sum(x>0 for x in slopes),
        "negative_individual_slope_count":sum(x<0 for x in slopes),
        "mean_seasonal_day_minus_night_collar_temperature_gradient_change_C":mean(x["delta_thermal_day_vs_night"] for x in values),
        "mean_seasonal_day_collar_temperature_change_C":mean(x["delta_thermal_day"] for x in values),
        "mean_seasonal_night_collar_temperature_change_C":mean(x["delta_thermal_night"] for x in values),
        "mean_sensor_complete_paired_seasonal_relative_GPS_speed_shift_log1p":mean(x["delta_relative_gps_movement"] for x in values),
        "warning":"Collar external temperature is mixed electronics/body/ambient heat, validated only as RELATIVE thermal landscape sensor. No causal mechanism or global generality."
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    if c["version"]!="kruger-collar-thermal-diel-solar-pair-v0":raise ValueError("Missing frozen protocol")
    src=json.loads(SOURCE.read_text(encoding="utf-8"))["source"]
    report={"study":"Kruger independent elephant within-individual ecological calendar/relative thermal indicator",
            "source_doi":src["doi"],"original_cc0":src["license"],
            "previous_hourly_movement_source_effect":-0.028893655483298752}
    dest=a.out/"kruger_original.csv"
    try:
        candidates=[x for x in original_files(src["package_uuid"]) if x["bitstream_uuid"]==src["original_bitstream_uuid"]]
        if len(candidates)!=1 or candidates[0]["checksum"]["value"].lower()!=src["original_md5"].lower():
            raise ValueError("Frozen Kruger provider CSV UUID or MD5 mismatch")
        report["provider_original_integrity"]=checksum_and_download(candidates[0],dest)
        old=south.load_events
        try:
            south.load_events=thinned_loader
            replay=south.analyze_south(dest)
        finally:south.load_events=old
        prior=replay.get("effect",{}).get("mean_falling_minus_rising_log1p_night_over_day_kmh")
        if prior is None or abs(prior+0.028893655483298752)>1e-12 or replay.get("qualifying_distinct_individuals")!=13:
            raise ValueError("Predeclared GPS-only Kruger previous result replay FAILED before sensor values")
        report["original_GPS_movement_effect_reproduced"]=True
        tracks,counts=load_raw_thermal(dest)
        report["source_temperature_observation_coverage"]=counts
        years,sampling=source_solar_pairs(tracks)
        report["paired_solar_sampling"]=sampling
        report["collar_temperature_link"]=estimate(years)
        report["status"]="thermal_paired_source_completed"
    except Exception as ex:
        report.update(status="source_hold",error=f"{type(ex).__name__}: {ex}")
    finally:dest.unlink(missing_ok=True)
    print("KRUGER_THERMAL_SOLAR_ECOLOGY "+json.dumps(report,sort_keys=True),flush=True)
    (a.out/"kruger_collar_thermal_solar_results.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
if __name__=="__main__":main()
