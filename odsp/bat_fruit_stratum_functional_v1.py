"""Source-authenticated 3-level observed bat×fruit×capture-stratum information.

This is a **source-open exploratory aggregated contingency table**.
No individual bats, GPS heights, feeding locations, site/night holdout, or
species×layer mist-net catchability adjustment can be inferred.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import random
from typing import Mapping
from urllib.request import Request,urlopen

ORIGINAL_REPO="karolportosupi/Bat-fruit-interaction"
ORIGINAL_GIT_COMMIT="3d4ede895b9c5c2b9419f94458e3badb7440d932"
SOURCE_FILES={
    "canopy":("Matriz_dossel.txt","47676a5696d5d00b869b95aa8a4c0055297410d7"),
    "subcanopy":("Matriz_sub-dossel.txt","9a3fe231f611914a88bb09eb6ecb6d97d294aac2"),
    "understory":("Matriz_sub-bosque.txt","a2c51fce68cac27f920f5cace74395521db1f6af"),
    "pooled":("Matriz_tres_estratos.txt","bba476c853eca0602b6321055ec3ce53e2aed60b"),
}
EXPECTED_LAYER_TOTALS={"canopy":61,"subcanopy":109,"understory":154}
EXPECTED_TOTAL=324
EXPECTED_BAT_LABELS=9
EXPECTED_PLANT_LABELS=37
EXPECTED_POOLED_POSITIVE_PAIRS=89
N_PERMUTATIONS=1999
PRIMARY_SEED=20261123
COMPLEMENT_SEED=20261124


def source_git_sha1(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()


def parse_author_matrix(raw:bytes)->tuple[dict[tuple[str,str],int],dict]:
    data=raw.decode("utf-8-sig")
    reader=csv.reader(io.StringIO(data,newline=""),delimiter="\t")
    header=next(reader)
    if not header or header[0].strip() or len(header)<3:
        raise ValueError("original file requires blank first header, >=2 bats")
    bats=[x.strip() for x in header[1:]]
    if not all(bats) or len(bats)!=len(set(bats)):
        raise ValueError("source duplicate, blank bat or ambiguous name")
    counts={}
    plant_names=set()
    nonzero=0
    nrows=0
    for vals in reader:
        if not vals or not any(x.strip() for x in vals):
            continue
        if len(vals)!=len(bats)+1:
            raise ValueError("row width does not match original bat header")
        plant=vals[0].strip()
        if not plant or plant in plant_names:
            raise ValueError("duplicate or empty source plant label")
        plant_names.add(plant)
        nrows+=1
        for b,value in zip(bats,vals[1:]):
            s=value.strip()
            if not s.isdecimal():
                raise ValueError("original interaction count must be nonnegative integer")
            number=int(s)
            counts[(b,plant)]=number
            nonzero+=number>0
    if not counts or nrows<2:
        raise ValueError("too few original source plant rows")
    return counts,{"bat_count":len(bats),"plant_count":len(plant_names),
                   "row_count":nrows,"total":sum(counts.values()),
                   "nonzero_bat_plant_cells":nonzero,
                   "bat_names":bats,"plant_names":sorted(plant_names)}


def fetch_original_tables():
    archive={}
    for layer,(file_name,expected_blob) in SOURCE_FILES.items():
        url=(f"https://raw.githubusercontent.com/{ORIGINAL_REPO}/"
             f"{ORIGINAL_GIT_COMMIT}/{file_name}")
        req=Request(url,headers={"User-Agent":"odsp-bat-fruit-3strata-v1/1.0"})
        with urlopen(req,timeout=120) as stream:
            raw=stream.read(200_000)
        blob=source_git_sha1(raw)
        if blob!=expected_blob:
            raise ValueError(f"original Git blob changed/mismatched: {file_name}")
        table,details=parse_author_matrix(raw)
        archive[layer]={"counts":table,"details":details,
                        "source_git_blob_sha1":blob,
                        "source_file_sha256":hashlib.sha256(raw).hexdigest(),
                        "original_file_bytes":len(raw)}
    return archive


def audit_author_tensor(archive):
    expected=set(EXPECTED_LAYER_TOTALS)
    if set(archive)!=(expected|{"pooled"}):
        raise ValueError("four expected original tables required")
    for z,expected_count in EXPECTED_LAYER_TOTALS.items():
        if archive[z]["details"]["total"]!=expected_count:
            raise ValueError(f"original {z} count total does not reconcile")
    pooled=archive["pooled"]["counts"]
    bat_names=set(archive["pooled"]["details"]["bat_names"])
    plant_names=set(archive["pooled"]["details"]["plant_names"])
    if (len(bat_names)!=EXPECTED_BAT_LABELS or len(plant_names)!=EXPECTED_PLANT_LABELS or
        archive["pooled"]["details"]["total"]!=EXPECTED_TOTAL or
        archive["pooled"]["details"]["nonzero_bat_plant_cells"]!=EXPECTED_POOLED_POSITIVE_PAIRS):
        raise ValueError("original author aggregated source schema or totals changed")
    expected_source_bats={
        "canopy":9,"subcanopy":9,"understory":8,
    }
    tensor={}
    for z in expected:
        source=archive[z]["counts"]
        actual_names=set(archive[z]["details"]["bat_names"])
        if (len(actual_names)!=expected_source_bats[z] or not actual_names.issubset(bat_names)):
            raise ValueError(f"unexpected {z} bat labels or source columns")
        if not set(archive[z]["details"]["plant_names"]).issubset(plant_names):
            raise ValueError(f"{z} source contains plants missing from author pooled matrix")
        for b in bat_names:
            for p in plant_names:
                # Missing author omitted column is a reconciled *source matrix*
                # zero only, NOT a claim of true organism absence.
                n=source.get((b,p),0)
                tensor[(b,p,z)]=n
    mismatches=[
        (b,p) for b in bat_names for p in plant_names
        if sum(tensor[(b,p,z)] for z in expected)!=pooled[(b,p)]
    ]
    if mismatches:
        raise ValueError(f"source layer matrices fail author pooled cellwise reconciliation for {len(mismatches)} cells")
    if sum(tensor.values())!=EXPECTED_TOTAL:
        raise ValueError("source layer event total does not match published author network")
    details={
        "source_repo":ORIGINAL_REPO,"source_commit_sha":ORIGINAL_GIT_COMMIT,
        "source_filenames_and_git_blobs": {
            z:{"file":SOURCE_FILES[z][0],
               "git_blob_sha1":archive[z]["source_git_blob_sha1"],
               "sha256":archive[z]["source_file_sha256"],
               "bytes":archive[z]["original_file_bytes"]}
            for z in SOURCE_FILES
        },
        "observed_network_interaction_frequencies":EXPECTED_TOTAL,
        "bat_acoustic_or_mistnet_species_labels":len(bat_names),
        "plant_source_taxa_or_unidentified_codes":len(plant_names),
        "pooled_bat_plant_positive_cells":EXPECTED_POOLED_POSITIVE_PAIRS,
        "layer_interaction_counts":dict(EXPECTED_LAYER_TOTALS),
        "all_333_pooled_bat_plant_cells_reconciled":True,
        "understory_author_omitted_one_bat_column_reconciled_by_pooled_zeros":True,
    }
    return tensor,details


def entropy(counts: Mapping[object,int])->float:
    total=sum(counts.values())
    if total<=0:
        raise ValueError("nonzero source mass required")
    return -math.fsum((n/total)*math.log(n/total) for n in counts.values() if n>0)


def unconditional_information(tensor:Mapping[tuple[str,str,str],int], a_axis:int,b_axis:int)->float:
    """I(A;B) on original frequency tensor with axes bat,plant,stratum."""
    if a_axis==b_axis or not 0<=a_axis<=2 or not 0<=b_axis<=2:
        raise ValueError("two distinct original axes required")
    count_a=Counter()
    count_b=Counter()
    joint=Counter()
    n=0
    for key,value in tensor.items():
        if value<0:raise ValueError("negative source count")
        if not value:continue
        count_a[key[a_axis]]+=value
        count_b[key[b_axis]]+=value
        joint[(key[a_axis],key[b_axis])]+=value
        n+=value
    result=math.fsum((v/n)*math.log((v*n)/(count_a[a]*count_b[b]))
                     for (a,b),v in joint.items())
    return max(0.0,result)


def conditional_information(tensor:Mapping[tuple[str,str,str],int],
                            a_axis:int,b_axis:int,conditioning_axis:int)->float:
    """I(A;B|C) = sum n_abc/N log(n_abc n_c / (n_ac n_bc))."""
    if set((a_axis,b_axis,conditioning_axis))!={0,1,2}:
        raise ValueError("three distinct original source axes required")
    total=sum(tensor.values())
    if total<=0 or any(v<0 for v in tensor.values()):
        raise ValueError("finite positive mass required")
    c=Counter()
    ac=Counter()
    bc=Counter()
    abc=Counter()
    for key,n in tensor.items():
        if n<=0:continue
        a,b,d=key[a_axis],key[b_axis],key[conditioning_axis]
        c[d]+=n
        ac[(a,d)]+=n
        bc[(b,d)]+=n
        abc[(a,b,d)]+=n
    value=math.fsum((n/total)*math.log(n*c[d]/(ac[(a,d)]*bc[(b,d)]))
                    for (a,b,d),n in abc.items())
    return max(0.,value)


def conditional_entropy(tensor, outcome_axis, conditioning_axes):
    """Weighted H(Y|X) from original count margins."""
    all_axes=set((outcome_axis,*conditioning_axes))
    if not all_axes.issubset({0,1,2}) or outcome_axis in conditioning_axes:
        raise ValueError("invalid axes")
    c=Counter(); joint=Counter()
    total=0
    for key,n in tensor.items():
        if n<=0:continue
        given=tuple(key[ax] for ax in conditioning_axes)
        joint[(given,key[outcome_axis])]+=n
        c[given]+=n
        total+=n
    if total<=0:raise ValueError("no counts")
    return -math.fsum((n/total)*math.log(n/c[given])
                      for (given,y),n in joint.items())


def source_metrics(tensor):
    hp_b=conditional_entropy(tensor,1,(0,))
    hp_bz=conditional_entropy(tensor,1,(0,2))
    hb_p=conditional_entropy(tensor,0,(1,))
    hb_pz=conditional_entropy(tensor,0,(1,2))
    primary=conditional_information(tensor,1,2,0)
    complementary=conditional_information(tensor,0,2,1)
    if abs((hp_b-hp_bz)-primary)>1e-10:
        raise RuntimeError("primary CMI independent entropy identity failed")
    if abs((hb_p-hb_pz)-complementary)>1e-10:
        raise RuntimeError("complementary CMI entropy identity failed")
    return {
        "observed_interaction_I_plant_stratum_given_bat_nats":primary,
        "observed_interaction_I_bat_stratum_given_plant_nats":complementary,
        "observed_interaction_I_bat_stratum_nats":unconditional_information(tensor,0,2),
        "observed_interaction_I_plant_stratum_nats":unconditional_information(tensor,1,2),
        "observed_interaction_I_bat_plant_nats":unconditional_information(tensor,0,1),
        "plant_partner_entropy_given_bat_nats":hp_b,
        "plant_partner_entropy_given_bat_and_capture_stratum_nats":hp_bz,
        "fraction_partner_entropy_reduced_by_capture_stratum":primary/hp_b if hp_b>0 else None,
        "primary_cmi_entropy_identity_error":abs((hp_b-hp_bz)-primary),
        "complement_cmi_entropy_identity_error":abs((hb_p-hb_pz)-complementary),
    }


def _shuffle_nulls(tensor,conditioning_axis,first_axis,second_axis,seed):
    """Fixed margins for C at each group: first-variable×group, second×group."""
    groups=defaultdict(lambda:{"first":[],"second":[]})
    for key,n in tensor.items():
        if n<=0:continue
        group=key[conditioning_axis]
        groups[group]["first"].extend([key[first_axis]]*n)
        groups[group]["second"].extend([key[second_axis]]*n)
    rng=random.Random(seed)
    out=[]
    for _ in range(N_PERMUTATIONS):
        shuffled=Counter()
        for group in sorted(groups):
            first=groups[group]["first"]
            second=list(groups[group]["second"])
            rng.shuffle(second)
            for a,b in zip(first,second):
                if (first_axis,second_axis,conditioning_axis)==(1,2,0):
                    key=(group,a,b)
                elif (first_axis,second_axis,conditioning_axis)==(0,2,1):
                    key=(a,group,b)
                else:
                    raise ValueError("unexpected frozen permutation axes")
                shuffled[key]+=1
        out.append(conditional_information(shuffled,first_axis,second_axis,conditioning_axis))
    return out


def _quantile(a,q):
    v=sorted(a)
    x=(len(v)-1)*q
    lo=math.floor(x);hi=math.ceil(x)
    return v[lo]+(x-lo)*(v[hi]-v[lo])


def null_report(observed, values,seed):
    if not values:raise ValueError("source null distribution missing")
    return {
        "monte_carlo_null": "exchangeable stratum tokens within frozen conditioning group",
        "permutations":len(values),
        "seed":seed,
        "observed_cmi_nats":observed,
        "null_mean_nats":sum(values)/len(values),
        "observed_minus_null_mean_nats":observed-sum(values)/len(values),
        "null_95th_nats":_quantile(values,.95),
        "null_99th_nats":_quantile(values,.99),
        "upper_tail_conditional_exchangeability_p":(1+sum(x>=observed-1e-12 for x in values))/(1+len(values)),
        "not_independent_bat_or_site_level_inference":True,
    }


def evaluate():
    original=fetch_original_tables()
    tensor,provenance=audit_author_tensor(original)
    measured=source_metrics(tensor)
    primary_null=_shuffle_nulls(tensor,0,1,2,PRIMARY_SEED)
    complement_null=_shuffle_nulls(tensor,1,0,2,COMPLEMENT_SEED)
    return {
        "status":"original_public_bat_fruit_three_strata_source_and_conditional_information_evaluated",
        "paper_doi":"10.1002/oik.11609",
        "original_record_role":"bat-fruit interactions associated with bat capture stratum",
        "results_post_source_open_exploratory":True,
        "original_GitHub_source":provenance,
        "observed_information":measured,
        "primary_null_plant_stratum_given_bat":null_report(
            measured["observed_interaction_I_plant_stratum_given_bat_nats"],
            primary_null,PRIMARY_SEED),
        "complement_null_bat_stratum_given_plant":null_report(
            measured["observed_interaction_I_bat_stratum_given_plant_nats"],
            complement_null,COMPLEMENT_SEED),
        "not_measured_fruit_consumption_height":True,
        "no_independent_sites_nights_or_biological_individuals":True,
        "mistnet_species_by_stratum_capture_probability_not_calibrated":True,
        "not_a_latent_3d_sdm":True,
    }


def main():
    result=evaluate()
    path=Path("results/bat_fruit_three_stratum_functional_v1.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "original_source":result["original_GitHub_source"],
        "observed_information":result["observed_information"],
        "primary_null":result["primary_null_plant_stratum_given_bat"],
        "complement_null":result["complement_null_bat_stratum_given_plant"],
        "not_latent_3d_or_heldout":True,
    },indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
