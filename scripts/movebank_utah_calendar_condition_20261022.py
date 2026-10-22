"""Utah original source: does a taxon difference in day/night GPS movement co-vary
with regional heat or climatic water balance AFTER controlling solar daylength?

Six source original q contrasts and six initial marginal ERA5 slopes must replay
before opening calendar-conditioned outcomes. All outcomes are observational.
Neither original GPS tracking nor exact geographic cell/month values are exported.
"""
import argparse,json,math
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import mean,pstdev

from scripts.movebank_native_ecology_20261019 import HERE,original_files,checksum_and_download,daylength
from scripts.movebank_utah_four_taxa_solar_20261019 import (
    extract_time_only_original_source,CONTRACT as UTAH_SOURCE
)
from scripts.movebank_utah_shared_spatial_20261019 import source_cell_month,cluster_interval
from scripts.movebank_utah_diel_photoperiod_20261019 import compare_sites
from scripts.movebank_utah_era5_climate_20261019 import get_monthly_era5,paired_environment

CONTRACT=HERE/"research/MOVEBANK_UTAH_CALENDAR_CONDITIONED_V0_20261022.json"

def residuals(values,covariates):
    """OLS projection residuals after centering; 0,1 or 2 covariates."""
    v=[float(x) for x in values]
    x=[a-mean(v) for a in v]
    if not covariates:return x
    z=[[float(y)-mean(c) for y in c] for c in covariates]
    if len(z)==1:
        den=sum(a*a for a in z[0])
        if den<=1e-12:return None
        slope=sum(a*b for a,b in zip(x,z[0]))/den
        return [a-slope*b for a,b in zip(x,z[0])]
    if len(z)!=2:raise ValueError("Only daylength or daylength+one other climatic predictor allowed")
    zz0=sum(a*a for a in z[0]);zz1=sum(a*a for a in z[1])
    cross=sum(a*b for a,b in zip(z[0],z[1]))
    det=zz0*zz1-cross*cross
    if zz0<=1e-12 or zz1<=1e-12 or det/(zz0*zz1)<.01:
        return None
    xy0=sum(a*b for a,b in zip(x,z[0]));xy1=sum(a*b for a,b in zip(x,z[1]))
    b0=(xy0*zz1-xy1*cross)/det
    b1=(xy1*zz0-xy0*cross)/det
    return [a-b0*t-b1*w for a,t,w in zip(x,z[0],z[1])]

def partial_slope(rows,predictor,controls,minimum_n=6,residual_sd=.25,minimum_daylength_sd=.2):
    """q difference (last column) on x while adjusting listed controls."""
    if len(rows)<minimum_n:return None
    x=[r[predictor] for r in rows]
    y=[r[3] for r in rows]
    cols=[[r[i] for r in rows] for i in controls]
    if 2 in controls and pstdev([r[2] for r in rows])<minimum_daylength_sd:
        return None
    rx=residuals(x,cols)
    ry=residuals(y,cols)
    if rx is None or ry is None or pstdev(rx)<residual_sd:
        return None
    d=sum(v*v for v in rx)
    if d<=1e-12:return None
    return sum(a*b for a,b in zip(rx,ry))/d

def block_results(sources_a,sources_b,weather):
    """Within-block contrasts, no public per-cell or animal data."""
    common=sorted(set(sources_a)&set(sources_b))
    blocks=defaultdict(list);complete=missing=0;matched_interannual=set()
    by_gy_month=defaultdict(dict)
    for lat,lon,year,month in common:
        climate=weather.get((lat,lon,year,month))
        if climate is None:missing+=1;continue
        v=sources_a[(lat,lon,year,month)][0]-sources_b[(lat,lon,year,month)][0]
        light=daylength(lat+.5,date(year,month,15))
        t=climate["temperature_mean"]
        w=climate["precip_minus_et0"]/100
        blocks[(lat,lon)].append((t,w,light,v,year,month))
        by_gy_month[(lat,lon,month)][year]=(t,w,light,v)
        complete+=1
    outputs={}
    for name,predictor,controls,sd,needed in [
        ("partial_temperature_daylength",0,[2],.25,6),
        ("partial_water_daylength",1,[2],.05,6),
        ("joint_temperature_given_daylength_water",0,[2,1],.25,8),
        ("joint_water_given_daylength_temperature",1,[2,0],.05,8),
        ("univariate_daylength",2,[],.2,6)
    ]:
        vals=[]
        for group in blocks.values():
            s=partial_slope(group,predictor,controls,minimum_n=needed,residual_sd=sd)
            if s is not None:
                # Predictor 1 already uses (P−ET0)/100, so its slope is already per 100 mm.
                # Multiplying again by 100 would invent an erroneous scaling.
                vals.append(s)
        outputs[name]={
           "geographic_blocks_with_estimable_slope":len(vals),
           "mean_equal_geographic_block_slope":mean(vals) if vals else None,
           "positive_blocks":sum(x>0 for x in vals),"negative_blocks":sum(x<0 for x in vals),
           "block_bootstrap_95_interval":cluster_interval(vals)
        }
    # Strict same calendar month across different years: L ~ unchanged.
    # One cell-month contributes at most one year pair, regardless of source animals.
    anomalies=defaultdict(list)
    for (lat,lon,month),records in by_gy_month.items():
        years=sorted(records)
        if len(years)<2:continue
        for y0,y1 in zip(years,years[1:]):
            a,b=records[y0],records[y1]
            if abs(b[2]-a[2])>.05:continue
            anomalies[(lat,lon)].append((b[0]-a[0],b[1]-a[1],b[3]-a[3]))
    n_pairs=sum(len(x) for x in anomalies.values())
    diffs={}
    for name,ix,sd in [("temperature_same_calendar_month",0,.25),("water_same_calendar_month",1,.05)]:
        vals=[]
        for records in anomalies.values():
            if len(records)<3:continue
            x=[r[ix] for r in records];y=[r[2] for r in records]
            if pstdev(x)<sd:continue
            xc=[a-mean(x) for a in x];yc=[a-mean(y) for a in y]
            den=sum(a*a for a in xc)
            if den<=1e-12:continue
            slope=sum(a*b for a,b in zip(xc,yc))/den
            # Water index was pre-scaled to 100 mm units when records were formed.
            vals.append(slope)
        diffs[name]={
            "blocks_with_estimable_slope":len(vals),
            "equal_geographic_block_mean_slope":mean(vals) if vals else None,
            "block_bootstrap_95_interval":cluster_interval(vals)
        }
    return {
      "weather_qualified_shared_grid_year_months":complete,
      "missing_weather_shared_grid_year_months":missing,
      "geographic_grid_blocks_with_weather":len(blocks),
      "same_cell_same_calendar_month_between_year_contrasts":n_pairs,
      "same_calendar_month_geographic_blocks":len(anomalies),
      "daylength_conditioned_and_joint":outputs,
      "interannual_fixed_calendar_month_check":diffs,
      "ceiling":"Within-1degree-cell and source-year/month observational slopes; no climate causal effect, latent activity or independent-population generality."
    }

def main():
    cli=argparse.ArgumentParser();cli.add_argument("--out",type=Path,required=True)
    args=cli.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    contract=json.loads(CONTRACT.read_text())
    if contract["version"]!="utah-six-pair-calendar-conditioned-ecology-v0":
        raise ValueError("Missing registered calendar-conditioned ecological contract")
    prior={("|".join(r["pair"])):r for r in contract["all_six_frozen_previous_results"]}
    source=json.loads(UTAH_SOURCE.read_text())["source"]
    report={
        "route":"same-public-Utah-GPS six original pairs, post-outcome exploratory solar-calendar adjustment",
        "source_doi":source["doi"],"original_source_results_replayed":False,
        "original_weather_associations_replayed":False,"six_pairs":[]
    }
    path=args.out/"provider_original_utah.zip"
    try:
        original=[r for r in original_files(source["package_uuid"]) if r["bitstream_uuid"]==source["original_bitstream_uuid"]]
        if len(original)!=1 or original[0]["checksum"]["value"].lower()!=source["original_md5"].lower():
            raise ValueError("Provider original ZIP MD5 changed")
        report["original_provider_md5"]=checksum_and_download(original[0],path)
        animals,counts,unknown=extract_time_only_original_source(path,source["catalog_taxa"])
        source_map={}
        for taxon in source["catalog_taxa"]:
            source_map[taxon]=source_cell_month(animals[taxon]);animals[taxon].clear()
        old=compare_sites({k:{cell:v[0] for cell,v in l.items()} for k,l in source_map.items()})
        if len(old)!=6:raise ValueError("Exactly six original pairs are required")
        for pair in old:
            prev=prior["|".join(pair["taxa"])]
            if pair["shared_1degree_calendar_month_cells"]!=prev["shared_months"]:
                raise ValueError("Original GPS source opportunity support changed")
            if abs(pair["diel_contrast_a_minus_b_on_common_cells"]-prev["q_difference"])>1e-11:
                raise ValueError("Original GPS species source effect changed")
        report["original_source_results_replayed"]=True
        allmonth=defaultdict(set)
        for i,a in enumerate(source["catalog_taxa"]):
            for b in source["catalog_taxa"][i+1:]:
                for lat,lon,year,month in set(source_map[a])&set(source_map[b]):
                    allmonth[(lat,lon)].add((year,month))
        environment={};receipts=[];weather_holds=0
        for cell,months in sorted(allmonth.items()):
            try:
                fields,receipt=get_monthly_era5(cell,months)
                for (year,month),value in fields.items():
                    environment[(*cell,year,month)]=value
                receipts.append(receipt)
            except Exception as exc:
                receipts.append({"status":"weather_source_hold","error_type":type(exc).__name__})
                weather_holds+=1
        report["ERA5_source_grid_count"]=len(allmonth)
        report["ERA5_missing_grid_count"]=weather_holds
        report["ERA5_response_sha256s"]=[x.get("sha256") for x in receipts if x.get("sha256")]
        # Replay earlier climate slopes using the exact earlier function and source.
        for i,a in enumerate(source["catalog_taxa"]):
            for b in source["catalog_taxa"][i+1:]:
                base=paired_environment(a,b,source_map,environment)
                original=prior[f"{a}|{b}"]
                if base["weather_supported_common_cell_months"]!=original["shared_months"]:
                    raise ValueError("Previously published ERA5 original climate opportunity support has changed")
                if abs(base["within_geogrid_mean_slope_q_per_C"]-original["marginal_temperature_slope_per_C"])>1e-7:
                    raise ValueError("Published unadjusted temperature source association changed")
                if abs(base["within_geogrid_mean_slope_q_per_100mm"]-original["marginal_PminusET0_slope_per100mm"])>1e-7:
                    raise ValueError("Published unadjusted water source association changed")
        report["original_weather_associations_replayed"]=True
        for i,a in enumerate(source["catalog_taxa"]):
            for b in source["catalog_taxa"][i+1:]:
                result={"taxa":[a,b],
                        "original_marginal_temp_slope_per_C":prior[f"{a}|{b}"]["marginal_temperature_slope_per_C"],
                        "original_marginal_P_minus_ET0_slope_per100mm":prior[f"{a}|{b}"]["marginal_PminusET0_slope_per100mm"]}
                result.update(block_results(source_map[a],source_map[b],environment))
                report["six_pairs"].append(result)
                print("UTAH_CALENDAR_CONDITIONED_PAIR "+json.dumps(result,sort_keys=True),flush=True)
        report["status"]="six_original_source_pairs_and_era5_marginals_replayed_calendar_conditioned_complete"
    except Exception as e:
        report.update(status="SOURCE_HOLD",error=f"{type(e).__name__}: {e}")
    finally:path.unlink(missing_ok=True)
    (args.out/"utah_calendar_conditioned_ecology.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("UTAH_CALENDAR_CONDITIONED_SUMMARY "+json.dumps({
        "status":report["status"],"prior_GPS_replayed":report["original_source_results_replayed"],
        "prior_climate_replayed":report["original_weather_associations_replayed"],
        "pairs":len(report["six_pairs"]),"weather_source_hold_grids":report.get("ERA5_missing_grid_count")
    },sort_keys=True))
if __name__=="__main__":main()
