#!/usr/bin/env python3
"""Database-first geographic pilot: equal modeled daylength, distinct climate.

No animal outcome, behavioral inference, land-area population estimate, or
biome classification. The land-only hash-selected roster is written BEFORE
weather is requested; failed points are retained and never replaced.
"""
from __future__ import annotations
import argparse, csv, hashlib, io, json, math, sqlite3, statistics, time, urllib.error, urllib.parse, urllib.request, zipfile
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment

LAND_URL='https://naciscdn.org/naturalearth/110m/physical/ne_110m_land.zip'
LAND_SHA='1926c621afd6ac67c3f36639bb1236134a48d82226dc675d3e3df53d02d2a3de'
API='https://archive-api.open-meteo.com/v1/archive'
START=date(2017,12,1); END=date(2023,6,30)
YEARS=range(2018,2023)
LATS=(-45,-30,-15,15,30,45,60)
FIELDS=('tmean','tmax','precip30','balance30')
API_FIELDS=('temperature_2m_mean','temperature_2m_max','precipitation_sum','et0_fao_evapotranspiration')
SEED='ODSP-macroclimate-20261019'

def fingerprint(raw):return hashlib.sha256(raw).hexdigest()
def jsonbytes(obj):return (json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()
def fixed_timezone(lon):
    h=math.floor(lon/15+.5)
    return ('Etc/GMT'+(f'{-h:+d}' if h else ''),h*3600)
def select_sites(candidates):
    groups=defaultdict(list)
    for c in candidates:
        if not c['eligible_land']:continue
        lat,lon=c['latitude'],c['longitude']; sector=0 if lon<-30 else 1 if lon<60 else 2
        rank=fingerprint(f'{SEED}|{lat:.2f}|{lon:.2f}'.encode())
        groups[(lat,sector)].append((rank,lon))
    out=[]
    for (lat,sector),values in sorted(groups.items()):
        rank,lon=min(values); tz,offset=fixed_timezone(lon)
        out.append(dict(site_id=f'grid_{lat:+03d}_{sector}',latitude=lat,longitude=lon,sector=sector,selection_hash=rank,timezone=tz,utc_offset_seconds=offset))
    return out

def get_bytes(url,cap=5000000):
    for attempt in range(2):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'ODSP academic macroclimate pilot/0.1','Accept':'*/*'})
            with urllib.request.urlopen(req,timeout=90) as h:raw=h.read(cap+1)
            if len(raw)>cap:raise ValueError('Response exceeds registered download budget')
            return raw
        except urllib.error.HTTPError as e:
            if e.code not in (429,500,502,503,504) or attempt:raise
            pause=int(e.headers.get('Retry-After','10'))
            if pause>90:raise
            time.sleep(max(10,pause))
        except (TimeoutError,urllib.error.URLError):
            if attempt:raise
            time.sleep(5)

def save_csv(path,rows):
    if not rows:return
    with path.open('w',newline='',encoding='utf-8') as h:
        w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def prepare(out):
    import shapefile
    from shapely.geometry import Point,shape
    from shapely.ops import unary_union
    out.mkdir(parents=True,exist_ok=True); (out/'raw').mkdir(exist_ok=True)
    raw=get_bytes(LAND_URL)
    if fingerprint(raw)!=LAND_SHA:raise ValueError('Natural Earth published checksum mismatch')
    (out/'raw'/'naturalearth_land.zip').write_bytes(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        reader=shapefile.Reader(shp=io.BytesIO(z.read('ne_110m_land.shp')),shx=io.BytesIO(z.read('ne_110m_land.shx')),dbf=io.BytesIO(z.read('ne_110m_land.dbf')))
        land=unary_union([shape(s.__geo_interface__) for s in reader.shapes()])
    rows=[]
    for lat in LATS:
        for j in range(48):
            lon=-176.25+7.5*j; point=Point(lon,lat)
            inside=land.contains(point); distance=point.distance(land.boundary)
            rows.append(dict(latitude=lat,longitude=lon,inside_land=inside,boundary_distance_degrees=distance,eligible_land=inside and distance>=.25))
    sites=select_sites(rows)
    snapshot=dict(protocol='SOLAR_SEASON_MACROCLIMATE_PILOT_20261019',land_sha256=LAND_SHA,candidates=len(rows),land_eligible_candidates=sum(r['eligible_land'] for r in rows),sites=sites)
    payload=jsonbytes(snapshot)
    (out/'registry.json').write_bytes(payload); (out/'registry.sha256').write_text(fingerprint(payload)+'\n')
    save_csv(out/'all_grid_candidates.csv',rows);save_csv(out/'selected_sites.csv',sites)
    print(json.dumps({'phase':'ROSTER_LOCKED_BEFORE_WEATHER','sites':len(sites),'candidate_points':len(rows),'registry_sha256':fingerprint(payload)}),flush=True)

def daylength(d,lat):
    leap=d.year%4==0 and (d.year%100!=0 or d.year%400==0)
    g=2*math.pi/(366 if leap else 365)*(d.timetuple().tm_yday-1)
    dec=.006918-.399912*math.cos(g)+.070257*math.sin(g)-.006758*math.cos(2*g)+.000907*math.sin(2*g)-.002697*math.cos(3*g)+.00148*math.sin(3*g)
    p=math.radians(lat); q=(math.cos(math.radians(90.833))-math.sin(p)*math.sin(dec))/(math.cos(p)*math.cos(dec))
    if not -1<=q<=1:raise ValueError('Polar day/night outside registered site scope')
    return 8*math.degrees(math.acos(q))

def assign_pairs(costs,caliper=2.):
    a=np.asarray(costs,float)
    if a.size==0:return []
    n,m=a.shape; penalty=(n+1)*(caliper+1)
    full=np.full((n,m+n),penalty);full[:,:m]=np.where(a<=caliper,a,penalty*3)
    ii,jj=linear_sum_assignment(full)
    return [(int(i),int(j),float(a[i,j])) for i,j in zip(ii,jj) if j<m and a[i,j]<=caliper]

def astronomical_pairs(lat,year):
    anchor=date(year,6 if lat>0 else 12,21)
    rising=[anchor-timedelta(days=k) for k in range(21,161)]
    falling=[anchor+timedelta(days=k) for k in range(21,161)]
    rl=[daylength(d,lat) for d in rising]; fl=[daylength(d,lat) for d in falling]
    matches=assign_pairs([[abs(r-f) for f in fl] for r in rl])
    return [(rising[i],falling[j],rl[i],fl[j],diff) for i,j,diff in matches]

def compare_cycle(site,year,days):
    rows=[]
    for r,f,lr,lf,diff in astronomical_pairs(site['latitude'],year):
        a=days.get(str(r),{}); b=days.get(str(f),{})
        valid=all(a.get(k) is not None and b.get(k) is not None for k in FIELDS)
        rec=dict(site_id=site['site_id'],year=year,rising_date=str(r),falling_date=str(f),daylength_rising_minutes=lr,daylength_falling_minutes=lf,mismatch_minutes=diff,valid=valid)
        rec.update({'delta_'+k:b[k]-a[k] if valid else None for k in FIELDS});rows.append(rec)
    usable=[r for r in rows if r['valid']]; ready=len(usable)>=60 and len(usable)>=.8*len(rows)
    s=dict(site_id=site['site_id'],latitude=site['latitude'],longitude=site['longitude'],year=year,astronomy_pairs=len(rows),valid_pairs=len(usable),status='qualified' if ready else 'insufficient_climate_support')
    s.update({'delta_'+k:statistics.mean(r['delta_'+k] for r in usable) if ready else None for k in FIELDS})
    return rows,s

def fetch_climate(site,out):
    params=dict(latitude=site['latitude'],longitude=site['longitude'],start_date=str(START),end_date=str(END),daily=','.join(API_FIELDS),models='era5',timezone=site['timezone'],elevation='nan',cell_selection='nearest')
    url=API+'?'+urllib.parse.urlencode(params); raw=get_bytes(url)
    obj=json.loads(raw); (out/'raw'/f"{site['site_id']}.json").write_bytes(raw)
    if obj.get('utc_offset_seconds')!=site['utc_offset_seconds']:raise ValueError('Fixed-offset time definition not reproduced')
    if abs(obj['latitude']-site['latitude'])>.26 or abs(obj['longitude']-site['longitude'])>.26:raise ValueError('Requested grid point not reproduced')
    daily=obj['daily']; expected=[str(START+timedelta(days=i)) for i in range((END-START).days+1)]
    if daily.get('time')!=expected:raise ValueError('Source daily calendar is incomplete or duplicated')
    for k in API_FIELDS:
        if len(daily[k])!=len(expected):raise ValueError('Weather variable length mismatch')
    units=obj.get('daily_units',{})
    if units.get('temperature_2m_mean')!='°C' or units.get('precipitation_sum')!='mm' or units.get('et0_fao_evapotranspiration')!='mm':raise ValueError('Unexpected source units')
    def val(k,i):
        v=daily[k][i]
        if v is None:return None
        if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v):raise ValueError('Nonfinite source value')
        return float(v)
    rows=[];days={}
    for i,d in enumerate(expected):
        t,tx,p,e=[val(k,i) for k in API_FIELDS]
        wp=[val('precipitation_sum',j) for j in range(max(0,i-29),i+1)]
        we=[val('et0_fao_evapotranspiration',j) for j in range(max(0,i-29),i+1)]
        ok=i>=29 and all(x is not None for x in wp+we)
        rec=dict(site_id=site['site_id'],date=d,tmean=t,tmax=tx,precip=p,et0=e,precip30=sum(wp) if ok else None,balance30=sum(a-b for a,b in zip(wp,we)) if ok else None)
        days[d]=rec; rows.append(rec)
    provenance=dict(site_id=site['site_id'],status='downloaded',request_url=url,response_sha256=fingerprint(raw),resolved_latitude=obj['latitude'],resolved_longitude=obj['longitude'],resolved_elevation=obj.get('elevation'),daily_rows=len(rows),error=None)
    return days,rows,provenance

def write_database(path,tables):
    if path.exists():path.unlink()
    con=sqlite3.connect(path)
    for name,rows in tables.items():
        if not rows:continue
        cols=list(rows[0]);types=[]
        for col in cols:
            v=next((r[col] for r in rows if r[col] is not None),None)
            types.append('INTEGER' if isinstance(v,(int,bool)) else 'REAL' if isinstance(v,float) else 'TEXT')
        con.execute('CREATE TABLE "'+name+'" ('+', '.join('"'+c+'" '+t for c,t in zip(cols,types))+')')
        con.executemany('INSERT INTO "'+name+'" VALUES ('+','.join('?' for _ in cols)+')',[tuple(r[c] for c in cols) for r in rows])
    con.commit(); assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok';con.close()

def collect(out):
    payload=(out/'registry.json').read_bytes()
    if fingerprint(payload)!=(out/'registry.sha256').read_text().strip():raise ValueError('Roster changed before climate access')
    registry=json.loads(payload); sites=registry['sites']; daily=[]; pairs=[]; cycles=[];sources=[]
    for site in sites:
        try: days,rows,prov=fetch_climate(site,out);daily.extend(rows)
        except Exception as e:
            days={};prov=dict(site_id=site['site_id'],status='unavailable',request_url=None,response_sha256=None,resolved_latitude=None,resolved_longitude=None,resolved_elevation=None,daily_rows=0,error=f'{type(e).__name__}: {str(e)[:200]}')
        sources.append(prov)
        for year in YEARS:
            pp,ss=compare_cycle(site,year,days);pairs.extend(pp);cycles.append(ss)
        print(json.dumps({'site':site['site_id'],'status':prov['status'],'error':prov['error']}),flush=True)
        time.sleep(1)
    site_summary=[]
    for site in sites:
        cs=[c for c in cycles if c['site_id']==site['site_id'] and c['status']=='qualified']
        r={**site,'qualified_cycles':len(cs),'warmer_cycles':sum(c['delta_tmean']>0 for c in cs),'cooler_cycles':sum(c['delta_tmean']<0 for c in cs),'water_balance_higher_cycles':sum(c['delta_balance30']>0 for c in cs)}
        r.update({k:statistics.mean(c[k] for c in cs) if cs else None for k in ('delta_tmean','delta_tmax','delta_precip30','delta_balance30')});site_summary.append(r)
    tables={'selected_sites':sites,'daily_climate':daily,'matched_pairs':pairs,'site_cycle_summary':cycles,'site_summary':site_summary,'source_provenance':sources}
    for name,rows in tables.items():save_csv(out/(name+'.csv'),rows)
    write_database(out/'solar_season_macroclimate.sqlite',tables)
    good=[r for r in cycles if r['status']=='qualified']
    q=CounterQuad(good)
    summary=dict(status='GEOGRAPHIC_ENVIRONMENTAL_PILOT_NOT_ANIMAL_INFERENCE',registry_sha256=fingerprint(payload),selected_sites=len(sites),sites_retrieved=sum(s['status']=='downloaded' for s in sources),daily_rows=len(daily),valid_site_cycles=len(good),site_cycles_total=len(cycles),astronomy_pairs=len(pairs),valid_climate_pairs=sum(r['valid'] for r in pairs),joint_sign_counts=q,site_summary=site_summary,failures=[r for r in sources if r['status']!='downloaded'],limits=['ERA5 reanalysis and derived reference ET0, not field microclimate or actual evaporation.','Fixed geographic pilot, not land-area-unbiased sample or independent biome enumeration.','Paired days and annual cycles are repeated/autocorrelated; no p-values or global population CI.','No animal, vegetation, behavior or camera source opened or changed.'])
    (out/'summary.json').write_bytes(jsonbytes(summary))
    (out/'README.txt').write_text('ODSP solar-season geographic environmental pilot, 2026-10-19.\nAttribution: Natural Earth (CC0); C3S/ECMWF ERA5 via Open-Meteo (CC BY 4.0 API data attribution).\nVariables: degrees Celsius; precipitation and reference ET0 mm; 30d P-ET0 is a climatic proxy, not measured soil moisture.\nAll selected grid points and failed cases retained. Fixed-offset source dates; local summer branches, <=2min modeled photoperiod matching.\nSQLite tables and CSVs correspond exactly. raw/ contains source snapshots; response hashes are local snapshot fingerprints.\nNo animal-effect estimation; neither recurring years nor daily pairs are independent ecological study regions.\n')
    print(json.dumps({k:summary[k] for k in ('status','selected_sites','sites_retrieved','daily_rows','valid_site_cycles','valid_climate_pairs','joint_sign_counts')}),flush=True)

def CounterQuad(rows):
    from collections import Counter
    return dict(Counter(('warmer' if r['delta_tmean']>0 else 'cooler' if r['delta_tmean']<0 else 'temperature_tie')+'_'+('water_balance_higher' if r['delta_balance30']>0 else 'water_balance_lower' if r['delta_balance30']<0 else 'water_balance_tie') for r in rows))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','collect']);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    (prepare if a.command=='prepare' else collect)(a.out)
if __name__=='__main__':main()
