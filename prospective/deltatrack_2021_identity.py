#!/usr/bin/env python3
"""Prospectively fixed DELTATRACK 2021 adapter; MEDGULL numerical kernel unchanged."""
from __future__ import annotations
import argparse, csv, gzip, hashlib, json, math, platform
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from pyproj import Transformer

TAXA=('Larus argentatus','Larus fuscus')
MD5='1a3145234cccd1a48b280b0fb485d679'
FILENAME='DELTATRACK-gps-2021.csv.gz'
EDGES=np.array([-np.inf,-200,-100,-50,-25,0,25,50,100,200,np.inf])
PLAN_COMMIT='abd6416013cf8aedf0acff9b91782964ce947228'


def verify_source(path):
    md=hashlib.md5();sh=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):md.update(b);sh.update(b)
    if Path(path).name!=FILENAME or md.hexdigest()!=MD5:
        raise ValueError('Frozen source filename/checksum mismatch')
    return {'md5':md.hexdigest(),'sha256':sh.hexdigest()}


def build_panels(rows):
    project=Transformer.from_crs('EPSG:4326','EPSG:32631',always_xy=True)
    first={}; counts={t:Counter() for t in TAXA}
    for r in rows:
        taxon=(r.get('individual-taxon-canonical-name') or '').strip()
        if taxon not in TAXA:continue
        counts[taxon]['raw_rows']+=1
        if any((r.get(k) or '').strip().lower() in {'true','t','1','yes','y'}
               for k in ('import-marked-outlier','manually-marked-outlier')):
            counts[taxon]['provider_outliers']+=1;continue
        t=(r.get('timestamp') or '').strip();a=(r.get('individual-local-identifier') or '').strip()
        try:
            yr,mo,hr,mi=int(t[:4]),int(t[5:7]),int(t[11:13]),int(t[14:16])
            lo,la,sp=float(r['location-long']),float(r['location-lat']),float(r['ground-speed'])
        except (KeyError,ValueError,TypeError):continue
        if yr!=2021 or mo not in (5,6,7) or not a:continue
        if not(0<=hr<24 and 0<=mi<60 and -180<=lo<=180 and -90<=la<=90 and 5<=sp<=55):continue
        x,y=project.transform(lo,la)
        if not(math.isfinite(x) and math.isfinite(y)):continue
        counts[taxon]['raw_flight_proxy_rows']+=1
        c=(math.floor(x/5000),math.floor(y/5000)); key=(taxon,a,t[:10],hr*12+mi//5)
        if key not in first or t<first[key][0]:first[key]=(t,c,r.get('height-above-msl',''))
    ev={t:defaultdict(list) for t in TAXA}
    for (taxon,a,d,_),(_,cell,rawz) in first.items():
        counts[taxon]['five_minute_bins']+=1
        try:z=float(rawz)
        except (ValueError,TypeError):counts[taxon]['missing_height']+=1;continue
        if not math.isfinite(z):counts[taxon]['missing_height']+=1;continue
        if not -300<=z<=3000:counts[taxon]['out_of_bounds']+=1;continue
        ev[taxon][a,d].append((cell,z));counts[taxon]['valid_height_bins']+=1
    panels={};quality={}
    for taxon in TAXA:
        sessions=[]
        for (a,d),events in sorted(ev[taxon].items()):
            h=np.array([z for _,z in events]);bins=np.searchsorted(EDGES,h-np.median(h),side='right')-1
            hist=defaultdict(lambda:np.zeros(10,np.int64))
            for (cell,z),b in zip(events,bins):hist[cell][b]+=1
            sessions.append({'animal':a,'day':d,'hist':dict(hist)})
        panels[taxon]=sessions
        q={k:int(counts[taxon][k]) for k in ('raw_rows','provider_outliers','raw_flight_proxy_rows',
            'five_minute_bins','missing_height','out_of_bounds','valid_height_bins')}
        q['valid_fraction']=q['valid_height_bins']/q['five_minute_bins'] if q['five_minute_bins'] else 0.
        q['sessions']=len(sessions);q['individuals']=len({a for a,d in ev[taxon]})
        quality[taxon]=q
    return panels,quality


def clean(value):
    if isinstance(value,dict):return {str(k):clean(v) for k,v in value.items() if k!='day_scored_bins'}
    if isinstance(value,(list,tuple)):return [clean(v) for v in value]
    if isinstance(value,np.ndarray):return clean(value.tolist())
    if isinstance(value,np.generic):return value.item()
    return value


def main():
    from . import medgull_sensitivity as engine
    import numba,pyproj
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gps',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    hashes=verify_source(args.gps)
    with gzip.open(args.gps,'rt',encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        required={'timestamp','location-long','location-lat','ground-speed',
                  'individual-local-identifier','individual-taxon-canonical-name','height-above-msl'}
        if not required<=set(reader.fieldnames or []):raise ValueError('Required native fields missing')
        panels,quality=build_panels(reader)
    report={'analysis':'DELTATRACK_2021_IDENTITY_V1','plan_commit':PLAN_COMMIT,
        'source_doi':'10.5281/zenodo.22102508','source_file':FILENAME,'source_hashes':hashes,
        'kernel_sha256':hashlib.sha256(Path(engine.__file__).read_bytes()).hexdigest(),
        'runtime':{'python':platform.python_version(),'numpy':np.__version__,'numba':numba.__version__,'pyproj':pyproj.__version__},
        'seed':20261021,'requested_permutations':999,'panels':{}}
    for taxon in TAXA:
        result={'quality':quality[taxon],'terminal':'unavailable','primary_upper_p':1.}
        report['panels'][taxon]=result
        if quality[taxon]['valid_fraction']<.8 or not panels[taxon]:
            result['reason']='native_altitude_quality';continue
        x=engine.pack(panels[taxon]);comparisons={}
        for d in (1,50):
            sup=engine.support(x,d)
            for w in ('balanced','pooled'):
                est=engine.evaluate(x,d,w)
                if not np.array_equal(sup['day_scored_bins'],est['day_scored_bins']):
                    raise AssertionError('Support and scoring masks differ')
                comparisons[f'D{d}_{w}']=clean(est)
        result['comparisons']=comparisons
        primary=comparisons['D1_balanced']
        print(json.dumps({'stage':'observed','taxon':taxon,'birds':primary['eligible_birds'],
            'bird_days':primary['eligible_days'],'scored_bins':primary['eligible_bins'],
            'gain':primary['mean_gain']},sort_keys=True),flush=True)
        if primary['eligible_birds']<10:
            result['reason']='minimum_ten_individuals';continue
        rng=np.random.default_rng(20261021);draws=[];counts=[];moved=[]
        with (args.out/(taxon.replace(' ','_')+'_null.csv')).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=['permutation','gain','eligible_birds','eligible_days','eligible_bins','fraction_labels_changed'])
            writer.writeheader()
            for j in range(999):
                labs=engine.permute_labels(x,rng);n,g=engine.kernel(x,1,labs,True)
                r=engine.summarise(x,n,g[1],labs)
                valid=r['eligible_birds']>=10 and r['mean_gain'] is not None and math.isfinite(r['mean_gain'])
                draws.append(r['mean_gain'] if valid else None);counts.append(r['eligible_birds'])
                moved.append(float(np.mean(labs!=x['labels'])))
                writer.writerow({'permutation':j+1,'gain':draws[-1],'eligible_birds':counts[-1],
                    'eligible_days':r['eligible_days'],'eligible_bins':r['eligible_bins'],
                    'fraction_labels_changed':moved[-1]})
                if (j+1)%100==0:print(taxon,'permutations',j+1,flush=True)
        cal=engine.calibrate(primary['mean_gain'],draws,999)
        result['calibration']=clean(cal)
        result['randomization']={'eligible_birds_range':[int(min(counts)),int(max(counts))],
            'mean_fraction_labels_changed':float(np.mean(moved)),
            'all_sessions':len(x['labels']),'dates_with_multiple_birds':sum(len(g)>1 for g in x['date_groups'])}
        if cal['valid']<950 or not any(v>0 for v in moved):
            result['reason']='null_support';continue
        result['primary_upper_p']=cal['p_upper'];result['terminal']='tested'
    ordered=sorted(TAXA,key=lambda t:report['panels'][t]['primary_upper_p']);running=0.
    for i,taxon in enumerate(ordered):
        result=report['panels'][taxon]
        running=max(running,min(1.,(2-i)*result['primary_upper_p']))
        result['holm_upper_p']=running
        if result['terminal']=='tested':
            positive=result['calibration']['observed_minus_valid_null_mean']>0
            result['terminal']='supported' if positive and running<.05 else 'not_supported'
    report['limits']=['Two gull species from one source, not two fully independent tracking studies.',
        'Date-exchangeability, non-additive tag errors, effort and unobserved behavior remain assumptions/confounds.',
        'Session medians use heldout data; shape matching rather than real-time absolute-altitude prediction.',
        '2020 exclusion and MEDGULL primary remain unchanged; no replacement year or threshold.',
        'No implication for adaptive partitioning, central-place cause or universal mammal-bird law.']
    out=args.out/'DELTATRACK_2021_IDENTITY_RESULT_V1.json'
    out.write_text(json.dumps(clean(report),indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({t:{'terminal':r['terminal'],'holm_upper_p':r['holm_upper_p'],
        'birds':r.get('comparisons',{}).get('D1_balanced',{}).get('eligible_birds'),
        'gain':r.get('comparisons',{}).get('D1_balanced',{}).get('mean_gain')}
        for t,r in report['panels'].items()},sort_keys=True),flush=True)

if __name__=='__main__':main()
