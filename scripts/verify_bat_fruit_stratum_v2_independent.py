#!/usr/bin/env python3
"""Independent v2 replay of public bat-fruit three-stratum CMI and two nulls.

Separate CSV / tensor / entropy / permutation engine, not importing the v1
source parser, CMI formulas or randomization implementation. Observational
interaction counts; not true feeding height nor a site-level SDM.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from urllib.request import Request,urlopen

import numpy as np

ORIGINAL_COMMIT="3d4ede895b9c5c2b9419f94458e3badb7440d932"
ROOT=f"https://raw.githubusercontent.com/karolportosupi/Bat-fruit-interaction/{ORIGINAL_COMMIT}/"
FILES={
    "canopy":("Matriz_dossel.txt","47676a5696d5d00b869b95aa8a4c0055297410d7"),
    "subcanopy":("Matriz_sub-dossel.txt","9a3fe231f611914a88bb09eb6ecb6d97d294aac2"),
    "understory":("Matriz_sub-bosque.txt","a2c51fce68cac27f920f5cace74395521db1f6af"),
    "pooled":("Matriz_tres_estratos.txt","bba476c853eca0602b6321055ec3ce53e2aed60b"),
}
PREVIOUS_SOURCE_PRIMARY=0.2581875907325644
PREVIOUS_SOURCE_COMPLEMENT=0.2449384764233592
N=1999


def get_source():
    tables={}
    for layer,(name,sha1_expected) in FILES.items():
        with urlopen(Request(ROOT+name,headers={
            "User-Agent":"odsp-independent-bat-fruit-cmi-v2/1.0",
        }),timeout=90) as response:
            raw=response.read(8000)
        sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        if sha!=sha1_expected:
            raise ValueError("published author Git blob mismatch")
        rd=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""),delimiter="\t")
        h=next(rd)
        if h[0].strip():
            raise ValueError("unlabeled source first column expected")
        bat_labels=[s.strip() for s in h[1:]]
        if len(bat_labels)!=len(set(bat_labels)):
            raise ValueError("duplicate source bat label")
        plant_counts={}
        for line in rd:
            if not line or not any(x.strip() for x in line):
                continue
            if len(line)!=len(h):
                raise ValueError("source row width mismatch")
            plant=line[0].strip()
            if not plant or plant in plant_counts:
                raise ValueError("invalid source plant")
            plant_counts[plant]={b:int(value) for b,value in zip(bat_labels,line[1:])}
        tables[layer]=plant_counts
    return tables


def make_cube(tables):
    pooled=tables["pooled"]
    plants=sorted(pooled)
    bats=sorted({b for row in pooled.values() for b in row})
    zones=("canopy","subcanopy","understory")
    if len(plants)!=37 or len(bats)!=9:
        raise ValueError("unexpected original study label count")
    cube=np.zeros((len(bats),len(plants),len(zones)),dtype=int)
    for zi,zone in enumerate(zones):
        for p,row in tables[zone].items():
            if p not in pooled:
                raise ValueError("stratum-specific unpooled plant label")
            for b,n in row.items():
                if b not in bats or n<0:
                    raise ValueError("stratum-specific invalid bat or negative count")
                cube[bats.index(b),plants.index(p),zi]=n
    ref=np.array([[pooled[p].get(b,0) for p in plants] for b in bats],dtype=int)
    if not np.array_equal(cube.sum(axis=2),ref):
        raise ValueError("all-source author pooled marginal mismatch")
    if tuple(cube.sum(axis=(0,1)))!=(61,109,154) or cube.sum()!=324:
        raise ValueError("source original 3-stratum counts changed")
    if int(np.count_nonzero(ref))!=89:
        raise ValueError("author pooled unique interaction link count changed")
    return cube


def h(counts):
    flat=np.asarray(counts,dtype=float).reshape(-1)
    total=flat.sum()
    if total<=0 or np.any(flat<0):
        raise ValueError("nonempty nonnegative original contingency required")
    vals=flat[flat>0]/total
    return float(-np.sum(vals*np.log(vals)))


def numbers(cube):
    # Independent entropy identity, no use of production MI formula.
    H_BP=h(cube.sum(axis=2))
    H_BZ=h(cube.sum(axis=1))
    H_PZ=h(cube.sum(axis=0))
    H_B=h(cube.sum(axis=(1,2)))
    H_P=h(cube.sum(axis=(0,2)))
    H_BPZ=h(cube)
    return {
        "primary_plant_layer_given_bat":H_BP+H_BZ-H_B-H_BPZ,
        "complement_bat_layer_given_plant":H_BP+H_PZ-H_P-H_BPZ,
        "H_bat_given_plant":H_BP-H_P,
        "H_bat_given_plant_layer":H_BPZ-H_PZ,
    }


def nulls_numpy(cube,conditioning="bat",seed=20261127,reps=N):
    rng=np.random.default_rng(seed)
    bat_n,plant_n,layer_n=cube.shape
    groups=[]
    if conditioning=="bat":
        for b in range(bat_n):
            # Original bat×plant and bat×layer margins are held exactly.
            xs=np.repeat(np.arange(plant_n),cube[b].sum(axis=1))
            zs=np.repeat(np.arange(layer_n),cube[b].sum(axis=0))
            if xs.size!=zs.size:
                raise ValueError("bat margin mismatch")
            groups.append((b,xs,zs))
    elif conditioning=="plant":
        for p in range(plant_n):
            # Original plant×bat and plant×layer margins are held exactly.
            xs=np.repeat(np.arange(bat_n),cube[:,p,:].sum(axis=1))
            zs=np.repeat(np.arange(layer_n),cube[:,p,:].sum(axis=0))
            if xs.size!=zs.size:
                raise ValueError("plant margin mismatch")
            groups.append((p,xs,zs))
    else:
        raise ValueError("unexpected conditioning axis")
    out=[]
    for _ in range(reps):
        table=np.zeros_like(cube)
        for group,xs,zs in groups:
            moved=rng.permutation(zs)
            if conditioning=="bat":
                np.add.at(table,(group,xs,moved),1)
            else:
                np.add.at(table,(xs,group,moved),1)
        out.append(numbers(table)["primary_plant_layer_given_bat" if conditioning=="bat"
                                  else "complement_bat_layer_given_plant"])
    return np.asarray(out)


def summarize(values,observed):
    n=len(values)
    return {
        "simulated_null_mean":float(values.mean()),
        "simulated_null_95th":float(np.quantile(values,.95)),
        "observed_minus_simulated_mean":float(observed-values.mean()),
        "one_sided_tail":float((1+np.sum(values>=observed-1e-12))/(n+1)),
    }


def main():
    cube=make_cube(get_source())
    calc=numbers(cube)
    diff_a=abs(calc["primary_plant_layer_given_bat"]-PREVIOUS_SOURCE_PRIMARY)
    diff_b=abs(calc["complement_bat_layer_given_plant"]-PREVIOUS_SOURCE_COMPLEMENT)
    if max(diff_a,diff_b)>1e-10:
        raise RuntimeError("independent 3D entropy identity conflicts with original v1")
    a=nulls_numpy(cube,conditioning="bat",seed=20261127)
    b=nulls_numpy(cube,conditioning="plant",seed=20261128)
    sa=summarize(a,calc["primary_plant_layer_given_bat"])
    sb=summarize(b,calc["complement_bat_layer_given_plant"])
    report={
        "status":"independent_threeway_entropy_and_nulls_replayed",
        "original_source_commit":ORIGINAL_COMMIT,
        "separate_original_file_parser":True,
        "uses_original_v1_CMI_or_permutation_functions":False,
        "source_observed_count":int(cube.sum()),
        "original_stratum_totals":list(map(int,cube.sum(axis=(0,1)))),
        "unique_original_bat_labels":int(cube.shape[0]),
        "unique_original_plant_labels":int(cube.shape[1]),
        "independent_tensor_entropy":calc,
        "difference_from_v1_primary_nats":diff_a,
        "difference_from_v1_complement_nats":diff_b,
        "null_primary_numpy_RNG_20261127":sa,
        "null_complement_numpy_RNG_20261128":sb,
        "null_permutations_each":N,
        "qualitative_original_v1_classifications_repeated":(
            sa["one_sided_tail"]>.05 and sb["one_sided_tail"]<=.05
        ),
        "not_independent_organisms_or_site_level_validation":True,
        "no_causal_resource_choice_or_true_fruit_eating_height":True,
    }
    output=Path("results/bat_fruit_stratum_v2_independent_replay.json")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
