"""Within-study four-ungulate diel movement and daylight ecology.

This is a NEW ecology question, NOT a rescue of the unsupported equal-
photoperiod opposite-season comparison. GPS tracks are never exported.
"""
import argparse,json,math,random
from collections import defaultdict
from pathlib import Path
from statistics import mean,median
from scripts.movebank_native_ecology_20261019 import HERE,original_files,checksum_and_download,daylength
from scripts.movebank_solar_movement_20261019 import valid_interval
from scripts.movebank_utah_four_taxa_solar_20261019 import (
    extract_time_only_original_source, CONTRACT as UTAH_SOURCE
)
CONTRACT=HERE/"research/MOVEBANK_UTAH_DIEL_PHOTOPERIOD_V0_20261019.json"

def slope(xy):
    if len(xy)<10:return None
    x=[a for a,b in xy];y=[b for a,b in xy]
    if max(x)-min(x)<0.5:return None
    xm=mean(x);ym=mean(y);den=sum((z-xm)**2 for z in x)
    if den<=1e-12:return None
    return sum((a-xm)*(b-ym) for a,b in xy)/den

def boot(a):
    if len(a)<5:return None
    rng=random.Random(20261019);n=len(a)
    draws=sorted(mean(a[rng.randrange(n)] for _ in range(n)) for _ in range(2000))
    return [draws[49],draws[1949]]

def one_taxon(name,animals):
    diel=[];grad=[]; n_days=n_steps=n_accepted=0
    bin_years={"short":0,"middle":0,"long":0}
    cells=defaultdict(lambda:defaultdict(list))
    for animal,original_hour_dict in animals.items():
        obs=sorted(original_hour_dict.values())
        source_days=defaultdict(lambda:{"day":[],"night":[],"lat":[],"lon":[]})
        for a,b in zip(obs,obs[1:]):
            n_steps+=1
            seg=valid_interval(a[0],a[1],a[2],b[0],b[1],b[2])
            if seg is None:continue
            d,part,kmph,h,lat=seg;n_accepted+=1
            x=source_days[d];x[part].append(kmph);x["lat"].append(lat)
            x["lon"].append((a[2]+b[2])/2)
        years=defaultdict(list)
        for d,day in source_days.items():
            if len(day["day"])<3 or len(day["night"])<3:continue
            lat=mean(day["lat"]);lon=mean(day["lon"])
            q=math.log1p(median(day["night"]))-math.log1p(median(day["day"]))
            years[d.year].append((d,daylength(lat,d),q,(math.floor(lat),math.floor(lon),d.year,d.month)))
            n_days+=1
        animal_diel=[]; animal_slope=[]
        for year,rows in years.items():
            if len(rows)<10:continue
            animal_diel.append(mean(r[2] for r in rows))
            s=slope([(r[1],r[2]) for r in rows])
            if s is not None:animal_slope.append(s)
            bins={"short":0,"middle":0,"long":0}
            for d,light,q,cell in rows:
                b="short" if light<11 else "middle" if light<14 else "long"
                bins[b]+=1
                cells[cell][animal].append(q)
            for b in bins:
                if bins[b]>0:bin_years[b]+=1
        if animal_diel:diel.append(mean(animal_diel))
        if animal_slope:grad.append(mean(animal_slope))
    # support selection on animal-date coverage only, not response sign
    spatial={}
    for cell,by_animal in cells.items():
        a=[mean(values) for values in by_animal.values() if len(values)>=3]
        if len(a)>=3:spatial[cell]=mean(a)
    def effect(values,units):
        if len(values)<5:return None
        return {"unit":units,"n_individuals":len(values),"mean":mean(values),
            "animal_bootstrap_95_percentile":boot(values),
            "individual_positive":sum(x>0 for x in values),
            "individual_negative":sum(x<0 for x in values)}
    return {"taxon":name,"total_original_animals":len(animals),
        "original_adjacent_hour_steps":n_steps,"qualified_daypart_step_observations":n_accepted,
        "animal_local_dates_with_day_and_night":n_days,
        "admitted_animals_diel":len(diel),"admitted_animals_photoperiod_slope":len(grad),
        "admitted_individual_years_by_photoperiod_bin":bin_years,
        "supported_geographic_yearmonth_cells":len(spatial),
        "day_night_speed_contrast":effect(diel,"NIGHT-DAY log1p observed step km/h"),
        "daylength_association":effect(grad,"change in log1p NIGHT-DAY step rate per hour daylight")},spatial

def compare_sites(sites):
    names=list(sites);result=[]
    for i,a in enumerate(names):
        for b in names[i+1:]:
            both=set(sites[a])&set(sites[b])
            vals=[sites[a][key]-sites[b][key] for key in both]
            result.append({"taxa":[a,b],"shared_1degree_calendar_month_cells":len(both),
                "diel_contrast_a_minus_b_on_common_cells":mean(vals) if len(vals)>=3 else None,
                "status":"supported_descriptive" if len(vals)>=3 else "unsupported"})
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    spec=json.loads(CONTRACT.read_text());assert spec["version"]=="utah-diel-photoperiod-description-v0"
    original=json.loads(UTAH_SOURCE.read_text())["source"]
    report={"source":"Utah UDWR four original taxa, source-registered",
        "previous_matched_photoperiod_route":"INELIGIBLE for all taxa, UNCHANGED",
        "source_doi":original["doi"],"taxa":[],"paired_spatiotemporal_cells":[]}
    z=args.out/"original_source.zip"
    try:
        fs=[f for f in original_files(original["package_uuid"]) if f["bitstream_uuid"]==original["original_bitstream_uuid"]]
        if len(fs)!=1 or fs[0]["checksum"]["value"].lower()!=original["original_md5"].lower():
            raise ValueError("Public source checksum not verified")
        report["source_original_verified"]=checksum_and_download(fs[0],z)
        taxa,counts,unknown=extract_time_only_original_source(z,original["catalog_taxa"])
        report["unknown_taxon_rows"]=unknown;spatial={}
        for name in original["catalog_taxa"]:
            res,cells=one_taxon(name,taxa[name]);res["original_source_records"]=counts[name]["rows"]
            report["taxa"].append(res);spatial[name]=cells
            taxa[name].clear()
            print("UTAH_DIEL_TAXON_RESULT "+json.dumps(res,sort_keys=True),flush=True)
        report["paired_spatiotemporal_cells"]=compare_sites(spatial)
        report["status"]="original_source_four_taxon_descriptive_ecology_completed"
    except Exception as e:
        report.update(status="source_hold",error=f"{type(e).__name__}: {e}")
        if not report["taxa"]:
            report["taxa"]=[{"taxon":x,"day_night_speed_contrast":None,"daylength_association":None,"status":"source_hold"} for x in original["catalog_taxa"]]
    finally:z.unlink(missing_ok=True)
    (args.out/"utah_four_species_diel_photoperiod.json").write_text(json.dumps(report,indent=2)+"\n")
    print("UTAH_DIEL_SOURCE_SUMMARY "+json.dumps({"status":report["status"],
       "four_species":len(report["taxa"]),
       "diel_supported":sum(x.get("day_night_speed_contrast") is not None for x in report["taxa"]),
       "daylength_supported":sum(x.get("daylength_association") is not None for x in report["taxa"]),
       "shared_cellmonth_pairs_supported":sum(x["status"]=="supported_descriptive" for x in report["paired_spatiotemporal_cells"])},sort_keys=True))
if __name__=="__main__":main()
