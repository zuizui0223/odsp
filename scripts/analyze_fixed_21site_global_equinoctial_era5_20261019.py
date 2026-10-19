#!/usr/bin/env python3
"""Replay original source-frozen 21 land sites × three year equinox contrasts.
Reanalysis only; reject physically invalid soil moisture without substituting
models/sites/dates. No animal observation, causal or globally weighted inference.
"""
from __future__ import annotations
import csv
from collections import defaultdict
from datetime import date
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/solar_global_equinoctial_pilot_20261019'
FIELDS=('temperature_2m_mean','temperature_2m_max','soil_moisture_0_to_7cm_mean')
DATES={
 'south':(('2018-09-26','2019-03-19'),('2019-09-22','2020-03-22'),('2020-09-25','2021-03-20')),
 'north':(('2018-03-19','2018-09-26'),('2019-03-19','2019-09-26'),('2020-03-19','2020-09-25'))
}
def daylength(day,latitude):
    n=366 if day.year%4==0 and (day.year%100!=0 or day.year%400==0) else 365
    g=2*math.pi/n*(day.timetuple().tm_yday-1)
    d=(.006918-.399912*math.cos(g)+.070257*math.sin(g)
       -.006758*math.cos(2*g)+.000907*math.sin(2*g)
       -.002697*math.cos(3*g)+.00148*math.sin(3*g))
    p=math.radians(latitude)
    c=(math.cos(math.radians(90.833))-math.sin(p)*math.sin(d))/(math.cos(p)*math.cos(d))
    if abs(c)>1:raise ValueError('HOLD_POLAR_DAYLIGHT')
    return 8*math.degrees(math.acos(c))

def validate(obj,lat,lon,day):
    if abs(obj['latitude']-lat)>.4 or abs(obj['longitude']-lon)>.4:
        raise ValueError('HOLD_UNEXPECTED_GRID')
    if not obj.get('timezone') or obj.get('daily',{}).get('time')!=[day]:
        raise ValueError('HOLD_DATE_OR_TIMEZONE')
    units=obj.get('daily_units',{})
    if any(units.get(k)!='°C' for k in FIELDS[:2]) or units.get(FIELDS[2]) not in ('m³/m³','m3/m3'):
        raise ValueError('HOLD_SOURCE_UNITS')
    values=[]
    for k in FIELDS:
        seq=obj['daily'].get(k)
        if (not isinstance(seq,list) or len(seq)!=1 or isinstance(seq[0],bool)
            or not isinstance(seq[0],(int,float)) or not math.isfinite(seq[0])):
            raise ValueError('HOLD_MISSING_OR_NONFINITE')
        values.append(float(seq[0]))
    if values[1]<values[0]:raise ValueError('HOLD_INCONSISTENT_TEMPERATURE')
    if not 0<=values[2]<=1:raise ValueError('HOLD_PHYSICALLY_INVALID_SOIL_MOISTURE')
    return values

def desc(xs):
    return {'n':len(xs),'mean':mean(xs) if xs else None,
            'min':min(xs) if xs else None,'max':max(xs) if xs else None,
            'positive':sum(x>0 for x in xs),'negative':sum(x<0 for x in xs),
            'zero':sum(x==0 for x in xs)}

def compute():
    with (BASE/'original_21_land_grid_sites.csv').open(encoding='utf-8',newline='') as h:
        sites=list(csv.DictReader(h))
    if len(sites)!=21 or len({r['cell_id'] for r in sites})!=21:raise ValueError('HOLD_FIXED_LAND_SAMPLE_CHANGED')
    for s in sites:s['latitude']=float(s['latitude']);s['longitude']=float(s['longitude'])
    rows=[]
    source_sha={}
    for hemisphere in ('south','north'):
        group=[s for s in sites if (s['latitude']<0)==(hemisphere=='south')]
        path=BASE/f'era5_{"southern" if hemisphere=="south" else "northern"}_6batches_original_source.json'
        raw=path.read_bytes();source_sha[hemisphere]=hashlib.sha256(raw).hexdigest()
        source=json.loads(raw)
        if (len(source['batches'])!=6 or source['hemisphere']!=hemisphere
            or source['protocol']!='GLOBAL_GRID_EQUINOX_ENVIRONMENT_PILOT_20261019'
            or source['original_site_order']!=[[s['latitude'],s['longitude']] for s in group]):
            raise ValueError('HOLD_ORIGINAL_BATCH_OR_GRID_ORDER_DRIFT')
        for i,(early,late) in enumerate(DATES[hemisphere]):
            a,b=source['batches'][2*i:2*i+2];yr=2018+i
            letter='S' if hemisphere=='south' else 'N'
            if (a['id'],a['date'],b['id'],b['date'])!=(f'{letter}{yr}_rising',early,f'{letter}{yr}_falling',late):
                raise ValueError('HOLD_FROZEN_YEAR_AND_PHOTOPERIOD_BRANCH_DRIFT')
            if len(a['original_response'])!=len(group) or len(b['original_response'])!=len(group):
                raise ValueError('HOLD_SOURCE_LOCATION_COUNT')
            for k,s in enumerate(group):
                r,f=a['original_response'][k],b['original_response'][k]
                dl_r=daylength(date.fromisoformat(early),s['latitude'])
                dl_f=daylength(date.fromisoformat(late),s['latitude'])
                mismatch=abs(dl_f-dl_r)
                if mismatch>1:raise ValueError('HOLD_ASTRONOMICAL_MATCH_DRIFT')
                row={**s,'hemisphere':hemisphere,'cycle':yr,'rising_date':early,'falling_date':late,
                     'modeled_daylength_rising_minutes':dl_r,'modeled_daylength_falling_minutes':dl_f,
                     'modeled_daylength_mismatch_minutes':mismatch,'status':'NUMERIC_SOURCE_NOT_VERIFIED',
                     'delta_tmean_C':None,'delta_tmax_C':None,'delta_soil_m3m3':None,'opposite_tmean_soil_sign':None}
                try:
                    x=validate(r,s['latitude'],s['longitude'],early)
                    y=validate(f,s['latitude'],s['longitude'],late)
                    if r['latitude']!=f['latitude'] or r['longitude']!=f['longitude']:
                        raise ValueError('HOLD_SELECTED_ERA5_GRID_CHANGED')
                    T=y[0]-x[0];M=y[2]-x[2]
                    row.update(status='VERIFIED_REANALYSIS_PAIR',delta_tmean_C=T,
                               delta_tmax_C=y[1]-x[1],delta_soil_m3m3=M,
                               opposite_tmean_soil_sign=T*M<0)
                except (ValueError,TypeError,KeyError) as ex:
                    row['status']=str(ex) if str(ex).startswith('HOLD_') else 'HOLD_SOURCE_SCHEMA_ERROR'
                rows.append(row)
    if len(rows)!=63 or len({(r['cell_id'],r['cycle']) for r in rows})!=63:
        raise ValueError('HOLD_ORIGINAL_63_PAIR_ROSTER_CHANGED')
    good=[r for r in rows if r['status']=='VERIFIED_REANALYSIS_PAIR']
    by_site=defaultdict(list)
    for r in good:by_site[r['cell_id']].append(r)
    sitesum=[]
    for s in sites:
        a=by_site[s['cell_id']]
        t=mean([r['delta_tmean_C'] for r in a]) if a else None
        soil=mean([r['delta_soil_m3m3'] for r in a]) if a else None
        sitesum.append({'cell_id':s['cell_id'],'lat':s['latitude'],'lon':s['longitude'],
                        'continent':s['continent'],'map_label':s['map_label'],
                        'n':len(a),'mean_delta_tmean_C':t,'mean_delta_soil_m3m3':soil,
                        'opposite_sign_site_mean':t*soil<0 if a else None,
                        'opposite_sign_cycles':sum(r['opposite_tmean_soil_sign'] for r in a),
                        'all_three_opposite':len(a)==3 and all(r['opposite_tmean_soil_sign'] for r in a)})
    regional={}
    for hemi in ('north','south'):
        a=[r for r in good if r['hemisphere']==hemi]
        regional[hemi]={'n_pairs':len(a),'delta_tmean_C':desc([r['delta_tmean_C'] for r in a]),
                        'delta_soil_m3m3':desc([r['delta_soil_m3m3'] for r in a]),
                        'opposite_sign_count':sum(r['opposite_tmean_soil_sign'] for r in a)}
    summary={'source':'Open-Meteo ERA5 2018–2021 12 original source batches',
             'original_source_file_sha256':source_sha,
             'frozen_21_site_three_cycle_source_frame':True,
             'planned_pairs':len(rows),'verified_pairs':len(good),
             'invalid_pairs':[{'cell_id':r['cell_id'],'cycle':r['cycle'],'reason':r['status']}
                              for r in rows if r['status']!='VERIFIED_REANALYSIS_PAIR'],
             'max_daylength_mismatch_minutes':max(r['modeled_daylength_mismatch_minutes'] for r in rows),
             'delta_tmean_C':desc([r['delta_tmean_C'] for r in good]),
             'delta_tmax_C':desc([r['delta_tmax_C'] for r in good]),
             'delta_soil_m3m3':desc([r['delta_soil_m3m3'] for r in good]),
             'opposite_temperature_soil_sign_pairs':sum(r['opposite_tmean_soil_sign'] for r in good),
             'site_mean_opposite_sign_count_including_partial':sum(r['opposite_sign_site_mean'] for r in sitesum),
             'complete_3_cycle_sites':sum(s['n']==3 for s in sitesum),
             'complete_3_cycle_site_means_opposite_sign':sum(s['opposite_sign_site_mean'] for s in sitesum if s['n']==3),
             'complete_3_cycle_sites_opposite_in_every_cycle':sum(s['all_three_opposite'] for s in sitesum),
             'by_hemisphere':regional,'sites':sitesum,
             'no_area_weighting_or_animal_behavior_inference':True,
             'no_p_values_or_ecological_population_confidence_intervals':True}
    return rows,summary

def main():
    rows,s=compute()
    out=ROOT/'results'
    out.mkdir(exist_ok=True)
    with (out/'global_equinoctial_ERA5_2018_2020_63pairs.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (out/'global_equinoctial_ERA5_2018_2020_source_summary.json').write_text(
        json.dumps(s,sort_keys=True,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:s[k] for k in ('planned_pairs','verified_pairs','invalid_pairs',
               'opposite_temperature_soil_sign_pairs','complete_3_cycle_sites',
               'complete_3_cycle_site_means_opposite_sign',
               'complete_3_cycle_sites_opposite_in_every_cycle',
               'max_daylength_mismatch_minutes')},sort_keys=True))
if __name__=='__main__':main()
