#!/usr/bin/env python3
"""Post-outcome Gyps COMMON versus bird-SPECIFIC thermal height response.

Diagnose whether bird-specific thermal-conditioned vertical distributions
predict target-day centered GPS heights beyond the thermal reaction measured
in OTHER biological birds of the SAME source study and calendar month.

Uses frozen source/height bins, cell=50km, donor day criteria and bird-month
Wstar labels. Do not treat result as independent confirmation or causal effect.
"""
from __future__ import annotations
from collections import Counter,defaultdict
import math

import numpy as np
from numba import njit


def build_shared_context(packed):
    """Sparse (cell,month,bird) donor groups with same-day exclusions."""
    index=packed["index"]
    bird_days=packed["bird_days"]
    n_rows=len(index)
    n_birds=len(packed["birds"])
    months=sorted({d[:7] for b,d in bird_days})
    month_id={month:i for i,month in enumerate(months)}
    sid_month=np.asarray([month_id[d[:7]] for b,d in bird_days],np.int64)
    keys=sorted({
        (int(index[r,3]),int(sid_month[int(index[r,4])]),int(index[r,1]))
        for r in range(n_rows)
    })
    group_id={key:i for i,key in enumerate(keys)}
    row_group=np.zeros(n_rows,dtype=np.int64)
    group_by_cell_month_bird={}
    row_by_cell_date_bird={}
    for r in range(n_rows):
        cell=int(index[r,3]);bird=int(index[r,1])
        session=int(index[r,4])
        date=bird_days[session][1]
        k=(cell,int(sid_month[session]),bird)
        row_group[r]=group_id[k]
        group_by_cell_month_bird[k]=group_id[k]
        same_key=(cell,date,bird)
        if same_key in row_by_cell_date_bird:
            raise ValueError("Duplicate source bird-date-cell histogram")
        row_by_cell_date_bird[same_key]=r
    ref_groups=np.full((n_rows,n_birds),-1,dtype=np.int64)
    ref_same_date=np.full((n_rows,n_birds),-1,dtype=np.int64)
    for r in range(n_rows):
        cell=int(index[r,3]);session=int(index[r,4]);date=bird_days[session][1]
        month=int(sid_month[session])
        for b in range(n_birds):
            ref_groups[r,b]=group_by_cell_month_bird.get((cell,month,b),-1)
            ref_same_date[r,b]=row_by_cell_date_bird.get((cell,date,b),-1)
    return {
        "row_group":row_group,"ref_groups":ref_groups,
        "ref_same_date":ref_same_date,"n_groups":len(keys),
        "n_birds":n_birds,
        "source_months":months
    }


@njit(cache=True)
def _shared_kernel(
    index,hist,other_support,session_bird,labels,
    row_group,reference_group,reference_same_date,n_groups,n_birds,n_pairs
):
    n_rows=len(index);n_sessions=len(labels)
    # Focal own-day-smoothed probability donor distributions, as prior model.
    focal_pool=np.zeros((n_pairs,10),np.float64)
    focal_w=np.zeros((n_pairs,2,10),np.float64)
    n_focal_pool=np.zeros(n_pairs,np.int64)
    n_focal_state=np.zeros((n_pairs,2),np.int64)
    n_focal_fix=np.zeros((n_pairs,2),np.int64)
    # Population source-group donor distribution, pooled and by climate state.
    pop_all=np.zeros((n_groups,10),np.float64)
    pop_w=np.zeros((n_groups,2,10),np.float64)
    pop_n_all=np.zeros(n_groups,np.int64)
    pop_n_w=np.zeros((n_groups,2),np.int64)
    pop_fix=np.zeros((n_groups,2),np.int64)
    # Own source row distributions used to delete same-date donor bird sessions.
    daypdf=np.zeros((n_rows,10),np.float64)
    for r in range(n_rows):
        pair=int(index[r,0]);session=int(index[r,4])
        group=int(row_group[r]);state=int(labels[session])
        n=0
        for k in range(10):n+=int(hist[r,k])
        if n<=0:continue
        n_focal_pool[pair]+=1;pop_n_all[group]+=1
        for k in range(10):
            v=(hist[r,k]+.5)/(n+5.0)
            daypdf[r,k]=v
            focal_pool[pair,k]+=v
            pop_all[group,k]+=v
            if state>=0:
                focal_w[pair,state,k]+=v
                pop_w[group,state,k]+=v
        if state>=0:
            n_focal_state[pair,state]+=1
            n_focal_fix[pair,state]+=n
            pop_n_w[group,state]+=1
            pop_fix[group,state]+=n

    gain_sum=np.zeros(n_sessions,np.float64)
    day_fix=np.zeros(n_sessions,np.int64)
    n_other_available=np.zeros(n_sessions,np.int64)
    for r in range(n_rows):
        pair=int(index[r,0]);session=int(index[r,4])
        state=int(labels[session])
        if state<0 or other_support[r]<10:continue
        n=0
        for k in range(10):n+=int(hist[r,k])
        if n_focal_pool[pair]<2 or n_focal_state[pair,state]<2:
            continue
        if (n_focal_fix[pair,state]-n<10 or
            n_focal_fix[pair,1-state]<10):
            continue

        # Other source animals are weighted by BIRD, then days within bird.
        # Require both high and low Wstar supported by >=2 other birds,
        # same 50km cell/month, excluding all same UTC date donor sessions.
        group_thermal=np.zeros(10,np.float64)
        group_pool=np.zeros(10,np.float64)
        usable_birds=0
        collective_fix_low=0
        collective_fix_high=0
        for b in range(n_birds):
            if b==int(index[r,1]):
                continue
            g=int(reference_group[r,b])
            if g<0:continue
            same=int(reference_same_date[r,b])
            s_n=-1
            same_fix=0
            if same>=0:
                s_session=int(index[same,4])
                s_n=int(labels[s_session])
                for k in range(10):same_fix+=int(hist[same,k])
            nn0=int(pop_n_w[g,0])-(1 if s_n==0 else 0)
            nn1=int(pop_n_w[g,1])-(1 if s_n==1 else 0)
            nf0=int(pop_fix[g,0])-(same_fix if s_n==0 else 0)
            nf1=int(pop_fix[g,1])-(same_fix if s_n==1 else 0)
            nall=int(pop_n_all[g])-(1 if same>=0 else 0)
            if nn0<1 or nn1<1 or nf0<10 or nf1<10 or nall<2:
                continue
            usable_birds+=1
            collective_fix_low+=nf0
            collective_fix_high+=nf1
            for k in range(10):
                minus=daypdf[same,k] if same>=0 else 0.0
                pool=(pop_all[g,k]-minus)/nall
                state_minus=daypdf[same,k] if same>=0 and s_n==state else 0.0
                context=(pop_w[g,state,k]-state_minus)/(nn0 if state==0 else nn1)
                group_pool[k]+=pool
                group_thermal[k]+=context
        if usable_birds<2 or collective_fix_low<10 or collective_fix_high<10:
            continue

        # Species-wide common thermal odds-ratio applied to own baseline.
        # Normalize to a categorical probability, compare to bird-specific.
        q_unnorm=np.zeros(10,np.float64)
        z=0.0;valid=True
        for k in range(10):
            own_day=daypdf[r,k]
            prior=(focal_pool[pair,k]-own_day)/(n_focal_pool[pair]-1)
            background=group_pool[k]/usable_birds
            wstar=group_thermal[k]/usable_birds
            if background<=0 or wstar<=0 or prior<=0:
                valid=False;break
            q_unnorm[k]=prior*wstar/background
            z+=q_unnorm[k]
        if not valid or z<=0:
            continue
        score=0.0
        for k in range(10):
            if hist[r,k]==0:continue
            focal_day=daypdf[r,k]
            p_ind=(focal_w[pair,state,k]-focal_day)/(n_focal_state[pair,state]-1)
            p_shared=q_unnorm[k]/z
            if p_ind<=0 or p_shared<=0:
                valid=False;break
            score+=hist[r,k]*(np.log(p_ind)-np.log(p_shared))
        if not valid:
            continue
        gain_sum[session]+=score
        day_fix[session]+=n
        n_other_available[session]+=n*usable_birds

    # Score equal days per climate state, equal states then equal birds.
    gain=np.zeros((n_birds,2),np.float64)
    days=np.zeros((n_birds,2),np.int64)
    fixes=np.zeros((n_birds,2),np.int64)
    donors=np.zeros((n_birds,2),np.float64)
    for s in range(n_sessions):
        state=int(labels[s]);n=int(day_fix[s])
        if state<0 or n<20:continue
        bird=int(session_bird[s])
        gain[bird,state]+=gain_sum[s]/n
        days[bird,state]+=1
        fixes[bird,state]+=n
        donors[bird,state]+=n_other_available[s]/n
    scores=np.full(n_birds,np.nan)
    nvalid=0;n_days=0;n_fixes=0;gain_total=0.0
    for b in range(n_birds):
        if days[b,0]<2 or days[b,1]<2:continue
        score=.5*(gain[b,0]/days[b,0]+gain[b,1]/days[b,1])
        scores[b]=score
        nvalid+=1;n_days+=days[b,0]+days[b,1]
        n_fixes+=fixes[b,0]+fixes[b,1]
        gain_total+=score
    return (
        gain_total/nvalid if nvalid else np.nan,
        nvalid,n_days,n_fixes,scores,days,fixes,donors
    )


def score_shared_vs_bird(packed,ctx,labels=None):
    if labels is None:labels=packed["labels"]
    labels=np.asarray(labels,dtype=np.int64)
    if labels.shape!=packed["labels"].shape:
        raise ValueError("Whole bird-day Wstar labels length changed")
    r=_shared_kernel(packed["index"],packed["hist"],packed["other_support"],
       packed["session_bird"],labels,ctx["row_group"],
       ctx["ref_groups"],ctx["ref_same_date"],ctx["n_groups"],
       ctx["n_birds"],packed["npairs"])
    return {
      "mean_gain":float(r[0]) if math.isfinite(r[0]) else None,
      "eligible_birds":int(r[1]),
      "eligible_bird_days":int(r[2]),
      "scored_fixes":int(r[3]),
      "per_bird":{
        packed["birds"][i]:{
          "gain":float(r[4][i]),
          "low_days":int(r[5][i,0]),
          "high_days":int(r[5][i,1]),
          "scored_fixes":int(r[6][i,0]+r[6][i,1]),
          "other_bird_day_support_proxy":float(.5*(
             r[7][i,0]/r[5][i,0]+r[7][i,1]/r[5][i,1]))
        }
        for i in range(len(packed["birds"])) if math.isfinite(r[4][i])
      }
    }
