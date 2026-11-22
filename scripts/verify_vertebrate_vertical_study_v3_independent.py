#!/usr/bin/env python3
"""Independent V3 verification of already-opened 62-study V2 CV.

Separate original CSV reader, NumPy matrix normalization and vectorized
training objective. DOES NOT import original v2 model, reader, profile
constructor, or scorer. These are author-standardized source height proxies,
not captured organism GPS heights or source-detection-corrected 3D SDMs.
"""
from __future__ import annotations
from collections import defaultdict, Counter
from urllib.request import Request, urlopen
from pathlib import Path
from statistics import mean
from math import isfinite
import csv, hashlib, io, json

import numpy as np

URL=("https://raw.githubusercontent.com/schefferslab/Vert-Strata-Meta/"
     "a68a2fca81407800855ea482f94104b425911232/"
     "data/stripped_data/analysis/data_joined.csv")
SHA256="028f5ad6371151a1cd5d89d2e2711711b4de383e24dd914a55e28b74aaa9cdc1"
ORIGINAL_BLOB="7b9c5b7e2b5722c7f4891853dc4fbc2e83db6b4c"
GRID=np.arange(-6,6.0000001,.25,dtype=float)
EXPECTED={
  "abundance":{"studies":54,"profiles":69,"all":0.019080241191041562,
               "bats":0.03591887357855384},
  "richness":{"studies":42,"profiles":58,"all":0.0020023805505994313,
              "bats":0.001666442965017984},
}
ORIGINAL_TAXA={"Amphibians","Bats","Birds","Small mammals"}
D=5.0


def fetch():
    with urlopen(Request(URL,headers={
        "User-Agent":"odsp-independent-studies-v3/1.0",
    }), timeout=120) as response:
        raw=response.read(2_000_001)
    if hashlib.sha256(raw).hexdigest()!=SHA256:
        raise RuntimeError("original source SHA256 changed")
    git_hash=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    if git_hash!=ORIGINAL_BLOB:
        raise RuntimeError("original Git blob changed")
    return raw


def profiles_independent(raw):
    records=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
    header=next(records)
    def index(name):
        return header.index(name)
    cols=[index(n) for n in (
        "link","study_id","taxa","biodiversity_metric",
        "mean_strata_height_p","corrected_biodiversity_metric_value"
    )]
    # This alternative implementation groups raw rows via distinct numerical
    # heights, independently averaging *values at same rounded height*.
    groups=defaultdict(list)
    n=0
    for fields in records:
        if len(fields)!=len(header):
            raise ValueError("original source row width changed")
        site,study,taxon,metric,h_s,y_s=(fields[i].strip() for i in cols)
        h=float(h_s); y=float(y_s)
        if (not isfinite(h) or not 0<=h<=1.000000001 or
            not isfinite(y) or y<0):
            raise ValueError("invalid source ecological target/normalized stratum")
        if taxon not in ORIGINAL_TAXA or metric not in {"abundance","richness"}:
            raise ValueError("unknown original source taxon/metric")
        groups[(site,metric)].append((study,taxon,round(h,8),y))
        n+=1
    if n!=1422 or len(groups)!=127:
        raise ValueError("source row/unit schema changed")
    prof=[]
    duplicate_groups=0
    extra_rows=0
    for (site,metric),rows in sorted(groups.items()):
        studios={r[0] for r in rows};taxa={r[1] for r in rows}
        if len(studios)!=1 or len(taxa)!=1:
            raise ValueError("source study or broad taxon mixed within site")
        keyed=defaultdict(list)
        for study,taxon,h,y in rows:keyed[h].append(y)
        if len(keyed)<2:continue
        extra=len(rows)-len(keyed)
        if extra:duplicate_groups+=1;extra_rows+=extra
        he=np.array(sorted(keyed),dtype=float)
        y=np.array([np.mean(keyed[h]) for h in he],dtype=float)
        if y.sum()<=0: raise ValueError("not a positive response profile")
        q=y/y.sum()
        # Matrix version: score for every fixed β without importing v2.
        logits=GRID[:,None]*he[None,:]
        rowmx=logits.max(axis=1)
        log_norm=np.log(np.exp(logits-rowmx[:,None]).sum(axis=1))+rowmx
        grid_log=(logits*q[None,:]).sum(axis=1)-log_norm
        prof.append({"study":next(iter(studios)),"site":site,"taxon":next(iter(taxa)),
                     "metric":metric,"height":he,"q":q,"grid_scores":grid_log})
    if len(prof)!=127 or duplicate_groups!=14 or extra_rows!=49:
        raise ValueError("original repeated-height geometry inconsistency")
    if len({p["study"] for p in prof})!=62:
        raise ValueError("original study roster changed")
    return prof


def real_score(p,beta):
    # Separate NumPy dot/sum path from V2 native Python fsum log score.
    x=np.array(p["height"])*float(beta)
    m=np.max(x)
    return float(np.dot(p["q"],x)-(m+np.log(np.exp(x-m).sum())))


def grid_fit(eligible):
    # For each candidate slope: equal study of mean per-site log scores.
    study_grid=defaultdict(list)
    for p in eligible:study_grid[p["study"]].append(p["grid_scores"])
    if not study_grid:raise RuntimeError("empty training profile")
    score_matrix=np.stack([np.mean(a,axis=0) for a in study_grid.values()])
    avg=np.mean(score_matrix,axis=0)
    optimum=max(range(len(GRID)),
                key=lambda i:(float(avg[i]),-abs(GRID[i]),-GRID[i]))
    return float(GRID[optimum])


def independently_score(raw):
    profiles=profiles_independent(raw)
    out={}
    for metric in ("abundance","richness"):
        source=[p for p in profiles if p["metric"]==metric]
        studies=sorted({p["study"] for p in source})
        if len(studies)<15:
            raise ValueError("not enough original studies for V2 endpoint")
        folds=[]
        for held in studies:
            train=[p for p in source if p["study"]!=held]
            test=[p for p in source if p["study"]==held]
            if any(p["study"]==held for p in train):
                raise RuntimeError("source heldout study leaked to model")
            bg=grid_fit(train)
            taxon=test[0]["taxon"]
            if any(p["taxon"]!=taxon for p in test):
                raise RuntimeError("heterogeneous taxon labels within study")
            matching=[p for p in train if p["taxon"]==taxon]
            nstudies=len({p["study"] for p in matching})
            beta1=(nstudies*grid_fit(matching)+D*bg)/(nstudies+D) if nstudies>=4 else bg
            b0=mean(real_score(p,bg) for p in test)
            b1=mean(real_score(p,beta1) for p in test)
            folds.append({"study":held,"taxon":taxon,"site_count":len(test),
                          "gain":b1-b0,"b0":b0,"b1":b1})
        macro=mean(f["gain"] for f in folds)
        bat=[f["gain"] for f in folds if f["taxon"]=="Bats"]
        goal=EXPECTED[metric]
        if (len(folds)!=goal["studies"] or len(source)!=goal["profiles"] or
            abs(macro-goal["all"])>1e-9 or abs(mean(bat)-goal["bats"])>1e-9):
            raise RuntimeError("independent replay conflicts with original frozen V2 scores")
        out[metric]={
            "heldout_original_studies":len(folds),
            "site_metric_profiles":len(source),
            "independent_equal_study_mean_gain":macro,
            "independent_bats_mean_gain":mean(bat),
            "positive_studies":sum(f["gain"]>0 for f in folds),
            "bats_positive_studies":sum(v>0 for v in bat),
            "max_abs_original_against_independent_gain":abs(macro-goal["all"]),
            "max_abs_original_against_independent_bat_gain":abs(mean(bat)-goal["bats"]),
        }
    return out


def main():
    values=independently_score(fetch())
    record={
        "status":"original_study_vertical_profile_independent_replay_agreement",
        "pinned_source_sha256":SHA256,
        "source_parser":"independent_csv_reader_numeric_numpy_vectorization",
        "imports_v2_engine":False,
        "uses_same_original_study_splits_and_predeclared_beta_grid":True,
        "results":values,
        "not_latent_species_level_3d_sdm":True,
    }
    path=Path("results/vertebrate_vertical_study_independent_v3.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(record,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(record,indent=2,sort_keys=True))


if __name__=="__main__":
    main()
