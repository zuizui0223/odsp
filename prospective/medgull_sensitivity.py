#!/usr/bin/env python3
"""Bounded POST-OUTCOME sensitivity of MEDGULL centered altitude shape.

Original n=9 primary remains closed. Data admission and scoring use one kernel.
The two D1 nulls permute whole sessions within exact dates, not individual fixes.
"""
from __future__ import annotations
import argparse, csv, gzip, hashlib, json, math
from collections import defaultdict
from pathlib import Path
import numpy as np
from numba import njit
from pyproj import Transformer

MD5='aea4ac8900f553e105e797e0553d84e7'
SHA256='ab2949f0fd09b3fe938ad3aea1bcba0fe897fd39d501b30d9480de5aa601c3f3'
EDGES=np.array([-np.inf,-200,-100,-50,-25,0,25,50,100,200,np.inf])


def center_bins(heights):
    h=np.asarray(heights,dtype=float)
    if h.ndim!=1 or len(h)==0 or not np.all(np.isfinite(h)):
        raise ValueError('Finite nonempty one-dimensional height vector required')
    return np.searchsorted(EDGES,h-np.median(h),side='right')-1


def pack(rows):
    rows=sorted(rows,key=lambda r:(r['day'],r['animal']))
    if not rows or len({(r['day'],r['animal']) for r in rows})!=len(rows):
        raise ValueError('Need unique bird-day sessions')
    ids=sorted({r['animal'] for r in rows}); idmap={a:i for i,a in enumerate(ids)}
    days=sorted({r['day'] for r in rows}); dm={d:i for i,d in enumerate(days)}
    cells=sorted({c for r in rows for c in r['hist']}); cm={c:i for i,c in enumerate(cells)}
    hist=[]; ss=[]; cc=[]
    lookup=np.full((len(rows),len(cells)),-1,dtype=np.int64)
    for s,r in enumerate(rows):
        for c,h in sorted(r['hist'].items()):
            h=np.asarray(h,dtype=np.int64)
            if h.shape!=(10,) or np.any(h<0): raise ValueError('Invalid histogram')
            if h.sum()==0: continue
            lookup[s,cm[c]]=len(hist);hist.append(h);ss.append(s);cc.append(cm[c])
    hist=np.asarray(hist,dtype=np.int64)
    if len(hist)==0: raise ValueError('No nonzero profiles')
    rs=np.asarray(ss,dtype=np.int64);rc=np.asarray(cc,dtype=np.int64)
    totals=np.bincount(rs,weights=hist.sum(1),minlength=len(rows)).astype(np.int64)
    di=np.array([dm[r['day']] for r in rows],dtype=np.int64)
    return {'hist':hist,'row_session':rs,'row_cell':rc,'lookup':lookup,'totals':totals,
            'labels':np.array([idmap[r['animal']] for r in rows],dtype=np.int64),
            'day_index':di,'ids':ids,'days':days,'cells':cells,
            'date_groups':[np.flatnonzero(di==i) for i in range(len(days))]}


@njit(cache=True)
def _kernel(hist,rs,rc,lookup,totals,labels,dayindex,nid,nday,ncell,donor_min,score_values):
    """Return one support mask and two score variants. Never score ineligible cells."""
    ns=len(labels);nr=len(hist);K=10
    byid=np.zeros((nid,ncell,K)); bycell=np.zeros((ncell,K));byday=np.zeros((nday,ncell,K))
    sump=np.zeros((nid,ncell,K)); nprof=np.zeros((nid,ncell),np.int64)
    daybird=np.full((nday,nid),-1,np.int64)
    for s in range(ns):daybird[dayindex[s],labels[s]]=s
    for r in range(nr):
        s=rs[r]
        if totals[s]<donor_min:continue
        a=labels[s];c=rc[r];d=dayindex[s];n=hist[r].sum()
        for k in range(K):
            v=hist[r,k];byid[a,c,k]+=v;bycell[c,k]+=v;byday[d,c,k]+=v
            if score_values:sump[a,c,k]+=(v+.5)/(n+5.)
        nprof[a,c]+=1
    ntest=np.zeros(ns,np.int64);gains=np.zeros((2,ns))
    for r in range(nr):
        s=rs[r]
        if totals[s]<50:continue
        a=labels[s];c=rc[r];d=dayindex[s]
        own=np.zeros(K);other=np.zeros(K)
        for k in range(K):
            target=hist[r,k] if totals[s]>=donor_min else 0
            own[k]=byid[a,c,k]-target
            other[k]=bycell[c,k]-byid[a,c,k]-byday[d,c,k]+target
        no=own.sum();nt=other.sum()
        if no<10 or nt<10:continue
        n=hist[r].sum();ntest[s]+=n
        if not score_values:continue
        own_day_count=nprof[a,c]-(1 if totals[s]>=donor_min else 0)
        qother=np.zeros(K);nb=0
        for b in range(nid):
            if b==a:continue
            bs=daybird[d,b];br=-1
            if bs>=0 and totals[bs]>=donor_min:br=lookup[bs,c]
            den=nprof[b,c]-(1 if br>=0 else 0)
            if den<=0:continue
            nb+=1
            bn=hist[br].sum() if br>=0 else 0
            for k in range(K):
                subtract=(hist[br,k]+.5)/(bn+5.) if br>=0 else 0.
                qother[k]+=(sump[b,c,k]-subtract)/den
        for k in range(K):
            if hist[r,k]==0:continue
            p=(own[k]+.5)/(no+5.);q=(other[k]+.5)/(nt+5.)
            gains[0,s]+=hist[r,k]*(np.log(p)-np.log(q))
            sub=(hist[r,k]+.5)/(n+5.) if totals[s]>=donor_min else 0.
            ps=(sump[a,c,k]-sub)/own_day_count
            qo=qother[k]/nb
            gains[1,s]+=hist[r,k]*(np.log(ps)-np.log(qo))
    for s in range(ns):
        if ntest[s]>=50:
            gains[0,s]/=ntest[s];gains[1,s]/=ntest[s]
        else:gains[0,s]=np.nan;gains[1,s]=np.nan
    return ntest,gains


def kernel(x,donor_min=1,labels=None,values=True):
    labs=x['labels'] if labels is None else np.asarray(labels,dtype=np.int64)
    if labs.shape!=x['labels'].shape or len(set(zip(labs,x['day_index'])))!=len(labs):
        raise ValueError('One label per session and one session per bird-date required')
    return _kernel(x['hist'],x['row_session'],x['row_cell'],x['lookup'],x['totals'],
                   labs,x['day_index'],len(x['ids']),len(x['days']),len(x['cells']),donor_min,values)


def summarise(x,ntest,gains,labels=None):
    labs=x['labels'] if labels is None else labels
    per={}
    for a,name in enumerate(x['ids']):
        ix=np.flatnonzero((labs==a)&(ntest>=50))
        if len(ix)>=2:
            per[name]={'days':len(ix),'bins':int(ntest[ix].sum()),
                       'gain':float(np.mean(gains[ix])) if gains is not None else None}
    return {'eligible_birds':len(per),'eligible_days':sum(v['days'] for v in per.values()),
            'eligible_bins':sum(v['bins'] for v in per.values()),'eligible_ids':sorted(per),
            'mean_gain':float(np.mean([v['gain'] for v in per.values()])) if per and gains is not None else None,
            'per_bird':per,'day_scored_bins':ntest.copy()}


def support(x,donor_min=1,labels=None):
    n,_=kernel(x,donor_min,labels,False)
    return summarise(x,n,None,labels)


def evaluate(x,donor_min=1,weighting='pooled',labels=None):
    if weighting not in ('pooled','balanced'):raise ValueError(weighting)
    n,g=kernel(x,donor_min,labels,True)
    return summarise(x,n,g[0 if weighting=='pooled' else 1],labels)


def permute_labels(x,rng):
    labels=x['labels'].copy()
    for ix in x['date_groups']:labels[ix]=rng.permutation(labels[ix])
    return labels


def calibrate(observed,draws,requested=999):
    if len(draws)!=requested:raise ValueError('Do not omit unavailable randomizations')
    v=np.array([z for z in draws if z is not None and np.isfinite(z)],float)
    m=requested-len(v); b=int(np.sum(v>=observed))
    return {'requested':requested,'valid':len(v),'unavailable':m,'tail_ge_observed':b,
            'p_lower':(1+b)/(requested+1),'p_upper':(1+b+m)/(requested+1),
            'valid_null_mean':float(v.mean()) if len(v) else None,
            'valid_null_quantiles':np.quantile(v,[.025,.5,.975]).tolist() if len(v) else [],
            'observed_minus_valid_null_mean':float(observed-v.mean()) if len(v) else None}


def load_source(path):
    md=hashlib.md5();sh=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):md.update(b);sh.update(b)
    if md.hexdigest()!=MD5 or sh.hexdigest()!=SHA256:raise ValueError('Pinned source checksum mismatch')
    trans=Transformer.from_crs('EPSG:4326','EPSG:32631',always_xy=True)
    first={};raw=0;outlier=0
    with gzip.open(path,'rt',encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        fields=set(reader.fieldnames or [])
        req={'timestamp','individual-local-identifier','location-long','location-lat','ground-speed','height-above-msl'}
        if not req<=fields:raise ValueError('Missing source fields')
        marks=fields&{'import-marked-outlier','manually-marked-outlier'}
        for r in reader:
            raw+=1
            if any(r.get(k,'').strip().lower() in ('true','t','1','yes','y') for k in marks):outlier+=1;continue
            t=r['timestamp'].strip();a=r['individual-local-identifier'].strip()
            try:
                yr,mo,hr,mi=int(t[:4]),int(t[5:7]),int(t[11:13]),int(t[14:16])
                lo,la,sp=float(r['location-long']),float(r['location-lat']),float(r['ground-speed'])
            except (ValueError,TypeError):continue
            if yr!=2022 or mo not in (5,6,7) or not a:continue
            if not (0<=hr<24 and 0<=mi<60 and -180<=lo<=180 and -90<=la<=90 and 5<=sp<=55):continue
            xx,yy=trans.transform(lo,la)
            if not math.isfinite(xx+yy):continue
            c=(math.floor(xx/5000),math.floor(yy/5000));key=(a,t[:10],hr*12+mi//5)
            if key not in first or t<first[key][0]:first[key]=(t,c,r['height-above-msl'])
    events=defaultdict(list);missing=0;bad=0
    for (a,d,_),(_,c,h) in first.items():
        try:z=float(h)
        except (TypeError,ValueError):missing+=1;continue
        if not math.isfinite(z):missing+=1;continue
        if not -300<=z<=3000:bad+=1;continue
        events[a,d].append((c,z))
    rows=[]
    for (a,d),ev in sorted(events.items()):
        hist=defaultdict(lambda:np.zeros(10,np.int64))
        for (c,z),bi in zip(ev,center_bins([h for _,h in ev])):hist[c][bi]+=1
        rows.append({'animal':a,'day':d,'hist':dict(hist)})
    valid=sum(len(ev) for ev in events.values())
    q={'raw_rows':raw,'provider_outliers':outlier,'five_minute_bins':len(first),
       'valid_height_bins':valid,'missing_height':missing,'height_out_of_bounds':bad,
       'valid_fraction':valid/len(first),'source_md5':MD5,'source_sha256':SHA256,
       'all_valid_sessions':len(rows),'long_sessions':int(sum(sum(v.sum() for v in r['hist'].values())>=50 for r in rows))}
    if q['valid_fraction']<.8:raise ValueError('Original quality gate fails')
    return pack(rows),q


def serializable(r):
    return {k:v for k,v in r.items() if k!='day_scored_bins'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gps',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    p.add_argument('--permutations',type=int,default=999)
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    x,q=load_source(args.gps)
    comparisons={};perbird=[]
    for d in (50,1):
        s=support(x,d)
        for w in ('pooled','balanced'):
            r=evaluate(x,d,w)
            if not np.array_equal(r['day_scored_bins'],s['day_scored_bins']):raise AssertionError('Preflight/scoring mismatch')
            name=f'D{d}_{w}';comparisons[name]=serializable(r)
            for a,v in r['per_bird'].items():perbird.append({'variant':name,'individual':a,**v})
    orig=comparisons['D50_pooled']
    if orig['eligible_birds']!=9 or orig['eligible_days']!=241 or abs(orig['mean_gain']-(-.014494591842618162))>1e-10:
        raise AssertionError('Original estimate not reproduced exactly; do not continue')
    rng=np.random.default_rng(20261020);null={w:[] for w in ('pooled','balanced')};nr=[];moved=[]
    for j in range(args.permutations):
        labels=permute_labels(x,rng);n,g=kernel(x,1,labels,True)
        moved.append(float(np.mean(labels!=x['labels'])))
        for z,w in enumerate(('pooled','balanced')):
            r=summarise(x,n,g[z],labels)
            null[w].append(r['mean_gain'] if r['eligible_birds']>=10 else None)
        nr.append(r['eligible_birds'])
        if (j+1)%100==0:print(f'Randomizations completed: {j+1}',flush=True)
    calibration={w:calibrate(comparisons['D1_'+w]['mean_gain'],null[w],args.permutations) for w in null}
    # Holm upper p values, no dropping failed calibration from the family.
    names=sorted(calibration,key=lambda w:calibration[w]['p_upper'])
    running=0.
    for rank,w in enumerate(names):
        running=max(running,min(1.,(2-rank)*calibration[w]['p_upper']))
        calibration[w]['holm_upper_p']=running
        calibration[w]['calibration_available']=comparisons['D1_'+w]['eligible_birds']>=10 and calibration[w]['valid']>=int(np.ceil(.95*args.permutations))
    report={'analysis':'POST_OUTCOME_MEDGULL_DONOR_SENSITIVITY_V1','primary_reopened':False,
      'plan_commit':'cdc516f04bef29be3f5a786ee78916fea90d104d','quality':q,'comparisons':comparisons,
      'exploratory_calibration':calibration,'randomization':{'draws':args.permutations,'seed':20261020,
      'unit':'whole bird-day session','stratum':'exact UTC date','eligible_birds_range':[int(min(nr)),int(max(nr))],
      'mean_fraction_labels_changed':float(np.mean(moved)),'total_sessions':len(x['labels']),
      'dates_with_two_or_more_birds':sum(len(g)>1 for g in x['date_groups'])},
      'original_primary_reproduced':True,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.out/'RESULT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    with (args.out/'per_bird.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['variant','individual','days','bins','gain']);w.writeheader();w.writerows(perbird)
    with (args.out/'null_draws.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['draw','eligible_birds','pooled','balanced','fraction_labels_changed'])
        for j in range(args.permutations):w.writerow([j+1,nr[j],null['pooled'][j],null['balanced'][j],moved[j]])
    np.savez_compressed(args.out/'processed_sessions.npz',**{k:v for k,v in x.items() if k not in ('date_groups','cells','ids','days')},ids=np.array(x['ids']),days=np.array(x['days']),cells=np.array(x['cells']))
    print(json.dumps({'comparisons':{n:{k:r[k] for k in ('eligible_birds','eligible_days','eligible_bins','mean_gain')} for n,r in comparisons.items()},'calibration':calibration},indent=2),flush=True)

if __name__=='__main__':main()
