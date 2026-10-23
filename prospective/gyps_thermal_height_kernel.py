#!/usr/bin/env python3
"""Gyps 50-km context prediction kernel for within-day-centered altitude shapes.

Do not conflate this new vertical-distribution endpoint with the original
Scacco et al. flight transport cost and flapping repeatability analyses.
Whole bird-day thermal states are permuted only within bird/year-month.
"""
from __future__ import annotations

from collections import Counter,defaultdict
import math
import numpy as np
from numba import njit

HEIGHT_EDGES=np.array([-np.inf,-200.,-100.,-50.,-25.,0.,25.,50.,100.,200.,np.inf])
MIN_DAY=20
MIN_STATE_DONOR=10
MIN_OTHER_DONOR=10
MIN_STATE_DAYS=2


def center_bins(values):
    a=np.asarray(values,dtype=np.float64)
    if a.ndim!=1 or len(a)==0 or not np.isfinite(a).all():
        raise ValueError("Height vector must be finite and nonempty")
    out=np.searchsorted(HEIGHT_EDGES,a-np.median(a),side="right")-1
    if np.any((out<0)|(out>9)):
        raise ValueError("Invalid altitude categories")
    return out


def pack_profiles(sessions,labels):
    sessions=sorted(sessions,key=lambda r:(r["bird"],r["day"]))
    if not sessions:raise ValueError("No bird-day profiles")
    bird_days=[(z["bird"],z["day"]) for z in sessions]
    if len(set(bird_days))!=len(bird_days):
        raise ValueError("Duplicate bird-date profiles")
    birds=sorted({b for b,d in bird_days})
    bird_id={b:i for i,b in enumerate(birds)}
    cellids=sorted({c for s in sessions for c in s["hists"]})
    cell_id={c:i for i,c in enumerate(cellids)}
    dates=sorted({d for b,d in bird_days})
    date_id={d:i for i,d in enumerate(dates)}
    pairs=sorted({(s["bird"],c) for s in sessions for c in s["hists"]})
    pair_id={k:i for i,k in enumerate(pairs)}
    row_idx=[];row_hist=[]
    for i,s in enumerate(sessions):
        for cell,h in sorted(s["hists"].items()):
            h=np.asarray(h,np.int64)
            if h.shape!=(10,) or np.any(h<0):
                raise ValueError("A profile must contain ten nonnegative counts")
            if h.sum()==0:continue
            row_idx.append([pair_id[s["bird"],cell],bird_id[s["bird"]],
                            date_id[s["day"]],cell_id[cell],i])
            row_hist.append(h)
    if not row_idx:raise ValueError("No positive source height counts")
    idx=np.asarray(row_idx,dtype=np.int64)
    hist=np.asarray(row_hist,dtype=np.int64)
    # Source label is -1 middle, 0 low, 1 high, and derived without heights.
    label=np.asarray([labels.get(z,-1) for z in bird_days],dtype=np.int64)
    if not np.all(np.isin(label,[-1,0,1])):raise ValueError("Unknown wind state")
    group=defaultdict(list)
    for i,(bird,day) in enumerate(bird_days):
        group[bird,day[:7]].append(i)
    groups=[np.asarray(v,np.int64) for k,v in sorted(group.items())]
    celltotal=Counter();birdcell=Counter();datecell=Counter()
    for r,h in zip(idx,hist):
        pair,bird,date,cell,s=map(int,r);n=int(h.sum())
        celltotal[cell]+=n;birdcell[bird,cell]+=n;datecell[date,cell]+=n
    others=np.zeros(len(hist),dtype=np.int64)
    for i,(r,h) in enumerate(zip(idx,hist)):
        pair,bird,date,cell,s=map(int,r)
        n=int(h.sum())
        others[i]=celltotal[cell]-birdcell[bird,cell]-datecell[date,cell]+n
        if others[i]<0:raise AssertionError("Other-bird different-date algebra negative")
    return dict(index=idx,hist=hist,other_support=others,
        session_bird=np.asarray([bird_id[b] for b,d in bird_days],dtype=np.int64),
        bird_days=bird_days,birds=birds,
        labels=label,groups=groups,npairs=len(pairs))


@njit(cache=True)
def kernel(index,hist,other_support,session_bird,labels,n_birds,n_pairs):
    # A day's contribution is smoothed and averaged per cell, not per GPS fix
    # across days, so a 200-fix day does not dominate a 20-fix donor day.
    ns=len(labels)
    pooled=np.zeros((n_pairs,10),np.float64)
    context=np.zeros((n_pairs,2,10),np.float64)
    npooled=np.zeros(n_pairs,np.int64)
    nstate=np.zeros((n_pairs,2),np.int64)
    fixes_state=np.zeros((n_pairs,2),np.int64)
    for i in range(len(index)):
        pair=int(index[i,0]);session=int(index[i,4])
        state=int(labels[session]);n=0
        for k in range(10):n+=hist[i,k]
        npooled[pair]+=1
        for k in range(10):
            p=(hist[i,k]+.5)/(n+5.0)
            pooled[pair,k]+=p
            if state>=0:context[pair,state,k]+=p
        if state>=0:
            nstate[pair,state]+=1
            fixes_state[pair,state]+=n

    daygain=np.zeros(ns,np.float64)
    dayfixes=np.zeros(ns,np.int64)
    for i in range(len(index)):
        pair=int(index[i,0]);session=int(index[i,4])
        state=int(labels[session])
        if state<0 or other_support[i]<MIN_OTHER_DONOR:
            continue
        n=0
        for k in range(10):n+=hist[i,k]
        if npooled[pair]<2 or nstate[pair,state]<2:
            continue
        if fixes_state[pair,state]-n<MIN_STATE_DONOR:
            continue
        if fixes_state[pair,1-state]<MIN_STATE_DONOR:
            continue
        g=0.0;can_score=True
        for k in range(10):
            if hist[i,k]==0:continue
            daily=(hist[i,k]+.5)/(n+5.0)
            pb=(pooled[pair,k]-daily)/(npooled[pair]-1)
            pc=(context[pair,state,k]-daily)/(nstate[pair,state]-1)
            if pb<=0 or pc<=0:
                can_score=False;break
            g+=hist[i,k]*(np.log(pc)-np.log(pb))
        if can_score:
            daygain[session]+=g;dayfixes[session]+=n
    gains=np.zeros((n_birds,2),np.float64)
    days=np.zeros((n_birds,2),np.int64)
    totalfix=np.zeros((n_birds,2),np.int64)
    for s in range(ns):
        st=int(labels[s])
        if st<0 or dayfixes[s]<MIN_DAY:continue
        bird=int(session_bird[s])
        gains[bird,st]+=daygain[s]/dayfixes[s]
        days[bird,st]+=1
        totalfix[bird,st]+=dayfixes[s]
    birdscore=np.full(n_birds,np.nan)
    n_birds_ok=0;n_day=0;n_fix=0;sumgain=0.0
    for bird in range(n_birds):
        if days[bird,0]<MIN_STATE_DAYS or days[bird,1]<MIN_STATE_DAYS:
            continue
        val=.5*(gains[bird,0]/days[bird,0]+gains[bird,1]/days[bird,1])
        birdscore[bird]=val
        n_birds_ok+=1;sumgain+=val
        n_day+=days[bird,0]+days[bird,1]
        n_fix+=totalfix[bird,0]+totalfix[bird,1]
    return (
        sumgain/n_birds_ok if n_birds_ok else np.nan,
        n_birds_ok,n_day,n_fix,birdscore,days,totalfix
    )


def score(packed,labels=None):
    if labels is None:labels=packed["labels"]
    labels=np.asarray(labels,np.int64)
    if len(labels)!=len(packed["bird_days"]):
        raise ValueError("One state per bird day required")
    s=kernel(packed["index"],packed["hist"],packed["other_support"],
        packed["session_bird"],labels,len(packed["birds"]),packed["npairs"])
    return {
        "mean_gain":float(s[0]) if math.isfinite(s[0]) else None,
        "eligible_birds":int(s[1]),"eligible_bird_days":int(s[2]),
        "scored_fixes":int(s[3]),
        "per_bird":{
           packed["birds"][i]:{
              "gain":float(s[4][i]),
              "low_days":int(s[5][i,0]),
              "high_days":int(s[5][i,1]),
              "scored_fixes":int(s[6][i,0]+s[6][i,1])
           }
           for i in range(len(packed["birds"])) if math.isfinite(s[4][i])
        }
    }


def permute_day_states(packed,rng):
    labels=packed["labels"].copy()
    for group in packed["groups"]:
        if len(group)>1:
            labels[group]=rng.permutation(packed["labels"][group])
    return labels


def calibrate(observed,draws):
    n=len(draws)
    if n==0:raise ValueError("Need nonempty frozen null family")
    val=[d["mean_gain"] for d in draws if d["mean_gain"] is not None]
    invalid=n-len(val)
    result={"requested":n,"valid":len(val),"unavailable":invalid,
            "p_upper":1.0,"null_mean":None,"observed_minus_null_mean":None}
    if observed["mean_gain"] is None or not val:return result
    tail=sum(s>=observed["mean_gain"]-1e-14 for s in val)
    return {**result,
      "tail_null_ge_observed":tail,
      "null_mean":float(np.mean(val)),
      "null_quantiles_025_50_975":[float(x) for x in np.quantile(val,[.025,.5,.975])],
      "observed_minus_null_mean":float(observed["mean_gain"]-np.mean(val)),
      "p_lower":(1+tail)/(n+1),
      "p_upper":(1+tail+invalid)/(n+1),
      "null_eligible_birds_range":[min(d["eligible_birds"] for d in draws),
                                    max(d["eligible_birds"] for d in draws)]
    }
