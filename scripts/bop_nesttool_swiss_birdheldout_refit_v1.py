#!/usr/bin/env python3
"""Frozen 2024 Swiss prepared-feature RF: year-heldout vs bird-heldout.

Not exact original NestTool ranger replication. All model decisions and eight
seeds were frozen before real RDS/HR/nest values were opened. Only aggregate
test metrics, not individual IDs, rows, predictions or labels, are exported.
"""
from __future__ import annotations
import argparse
from collections import Counter
from itertools import product
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_NESTTOOL_SWISS_BIRD_HELDOUT_REFIT_V1_CONTRACT.json"
FEATURES=(
    "sex","revisits_day","residence_time_day","age_cy",
    "revisits_night","residence_time_night","dist_max_day_to_max_night",
    "median_day_dist_to_max_night","relative_dist_max_day_to_max_night",
    "revisitsSettle","revisitsIncu1","revisitsIncu2","revisitsChick1","revisitsChick2",
    "timeSettle","timeIncu1","timeIncu2","timeChick1","timeChick2",
    "meandayrevisitsBrood","lastvisitDay","maxtimeawayBrood2km","maxtimeawayBrood",
    "tottime_nest","Dist99Chick2","Dist99Settle","Dist99Incu1","Dist99Incu2","Dist99Chick1",
    "MCP95Chick2","MCP95Chick1","MCP95Incu1","MCP95Settle","MCP95Incu2"
)
SEEDS=tuple(range(20261119,20261127))
TARGETS={"HR":{"positive":"yes","negative":"no"},"nest":{"positive":"nest","negative":"no nest"}}
HIST_EXPECT={"1":66,"2":51,"3":62,"4":56,"5":20,"6":2,"7":1}
EPS=1e-6

def load_frozen()->dict:
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    s=c.get("source",{})
    schema=c.get("source_schema_gate",{})
    protocol=c.get("modeling",{})
    limit=c.get("science_limits",{})
    if (
        c.get("contract_id")!="bop-nesttool-swiss-prepared-source-bird-heldout-refit-v1"
        or c.get("freeze_date")!="2026-11-19"
        or s.get("git_blob_sha1")!="fab942c0df8d6f77dc1db2bd2e2717681b9a3632"
        or s.get("source_bytes")!=53709803
        or s.get("commit")!="8fdf3884b5f6079afdffdc5c563c9050766670a4"
        or schema.get("required_exact_rows")!=697
        or schema.get("required_exact_distinct_bird_ids")!=258
        or schema.get("required_exact_group_histogram_1_to_7")!=HIST_EXPECT
        or tuple(schema.get("required_all_features",[]))!=FEATURES
        or schema.get("expected_target_columns")!=list(TARGETS)
        or protocol.get("seeds")!=list(SEEDS)
        or protocol.get("allowed_response_variables")!=list(TARGETS)
        or protocol.get("n_estimators")!=500
        or protocol.get("max_features")!=5
        or protocol.get("criterion")!="gini"
        or protocol.get("bootstrap") is not True
        or protocol.get("class_weight") is not None
        or protocol.get("train_frac")!=.7
        or protocol.get("probability_clip_epsilon")!=EPS
        or protocol.get("target_prevalence_source_inspected_only_after_predeclared_contract") is not True
        or protocol.get("test_labels_never_used_in_feature_imputation_tuning_or_split_selection") is not True
        or protocol.get("do_not_export_per_year_predicted_probs_or_actual_labels_or_animal_IDs") is not True
        or protocol.get("no_tuning_to_test_outcome") is not True
        or limit.get("historic_ODSP")!="empirical_state_prediction_mixed"
        or limit.get("redkite_external")!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        or limit.get("season_vs_bird_is_design_sensitivity_on_same_data_not_new_country_external_validation") is not True
    ):
        raise ValueError("frozen 2024-prepared-source versus true-bird holdout protocol drifted")
    return c

def exact_bird_group_train_mask(birds, target_ntrain:int, seed:int):
    """Random-order 0/1 subset-sum. No labels, covariates or bird keys exported."""
    import numpy as np
    ids=np.asarray(birds,dtype=str)
    groups=sorted(set(ids.tolist()))
    rng=np.random.default_rng(seed)
    order=rng.permutation(len(groups))
    ordered=[groups[int(i)] for i in order]
    sizes=[int((ids==name).sum()) for name in ordered]
    witness={0:None}
    for i,weight in enumerate(sizes):
        for available in sorted(tuple(witness),reverse=True):
            new=available+weight
            if new<=target_ntrain and new not in witness:
                witness[new]=(available,i)
    if target_ntrain not in witness:
        raise ValueError("HOLD_UNMATCHABLE_GROUP_COUNTS")
    chosen=set()
    current=target_ntrain
    while current>0:
        previous,index=witness[current]
        if index in chosen or previous>=current:
            raise ValueError("INVALID_SUBSET_SUM_WITNESS")
        chosen.add(index)
        current=previous
    selected={ordered[i] for i in chosen}
    train_mask=np.array([bird in selected for bird in ids],dtype=bool)
    if (
        int(train_mask.sum())!=target_ntrain
        or len(set(ids[train_mask])&set(ids[~train_mask]))!=0
        or not train_mask.any() or not (~train_mask).any()
    ):
        raise ValueError("BIRD_GROUP_SPLIT_NOT_INDEPENDENT_OR_NOT_EQUAL_SIZE")
    return train_mask

def random_year_train_mask(n:int,ntrain:int,seed:int):
    import numpy as np
    rng=np.random.default_rng(seed)
    train=np.zeros(n,dtype=bool)
    train[rng.permutation(n)[:ntrain]]=True
    return train

def _predictor_matrices(df,idx_train,idx_test):
    import numpy as np
    import pandas as pd
    train=df.iloc[idx_train]
    test=df.iloc[idx_test]
    cols=[]
    for feature in FEATURES:
        if feature=="sex":
            a=train["sex"].astype("string").str.lower().str.strip()
            b=test["sex"].astype("string").str.lower().str.strip()
            values=set(a.dropna())|set(b.dropna())
            if not values.issubset({"m","f",""}):
                raise ValueError("UNEXPECTED_SEX_CATEGORY")
            train_mode=a[a.isin(["m","f"])].mode()
            fill=train_mode.iloc[0] if len(train_mode) else "m"
            x=a.replace("",pd.NA).fillna(fill).map({"m":0.,"f":1.}).to_numpy(dtype=float)
            z=b.replace("",pd.NA).fillna(fill).map({"m":0.,"f":1.}).to_numpy(dtype=float)
        else:
            a=train[feature].astype("string").str.strip()
            b=test[feature].astype("string").str.strip()
            # Source invalid text never silently coerced to numeric missing.
            for q in (a,b):
                valid=q.notna() & ~q.isin(["","NA","NaN","Inf","-Inf"])
                if pd.to_numeric(q[valid],errors="coerce").isna().any():
                    raise ValueError("UNEXPECTED_NONNUMERIC_PREDICTOR_COLUMN")
            x=pd.to_numeric(a,errors="coerce").to_numpy(dtype=float)
            z=pd.to_numeric(b,errors="coerce").to_numpy(dtype=float)
            x[~np.isfinite(x)]=np.nan
            z[~np.isfinite(z)]=np.nan
            finite=x[np.isfinite(x)]
            median=float(np.median(finite)) if len(finite) else 0.
            x=np.where(np.isfinite(x),x,median)
            z=np.where(np.isfinite(z),z,median)
        cols.append((x,z))
    return np.stack([x for x,_ in cols],axis=1),np.stack([z for _,z in cols],axis=1)

def _metrics_from_probs(ytest,p,prior,train_n,test_birds,train_birds,overlap):
    import numpy as np
    from sklearn.metrics import roc_auc_score,balanced_accuracy_score
    q=np.clip(p,EPS,1-EPS)
    t=np.asarray(ytest,dtype=int)
    tp=np.where(t==1,q,1-q)
    p0=np.clip(float(prior),EPS,1-EPS)
    bp=np.where(t==1,p0,1-p0)
    accuracy=float(np.mean((q>=.5)==t))
    brier=float(np.mean((q-t)**2))
    ll=float(-np.mean(np.log(tp)))
    gain=float(np.mean(np.log(tp)-np.log(bp)))
    if len(set(t.tolist()))==2:
        auc=float(roc_auc_score(t,q))
        balanced=float(balanced_accuracy_score(t,(q>=.5).astype(int)))
    else:
        auc=None
        balanced=None
    return {
        "train_n":int(train_n),"test_n":len(t),
        "train_unique_bird_ids":int(train_birds),
        "test_unique_bird_ids":int(test_birds),
        "overlapping_bird_ids":int(overlap),
        "test_positive_fraction":round(float(np.mean(t)),6),
        "test_accuracy":round(accuracy,6),
        "test_balanced_accuracy":None if balanced is None else round(balanced,6),
        "test_roc_auc":None if auc is None else round(auc,6),
        "test_log_loss":round(ll,6),
        "test_brier":round(brier,6),
        "test_mean_log_score_gain_vs_training_prevalence":round(gain,6)
    }

def model_one_panel(df,target:str,mode:str,seed:int):
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    if target not in TARGETS or mode not in ("year_id","bird_id"):
        raise ValueError("NON_FROZEN_TARGET_OR_SPLIT_MODE")
    label=df[target].astype("string").str.strip().str.lower()
    legal=set(TARGETS[target].values())
    if not set(label.dropna()).issubset(legal|{""}):
        raise ValueError("HOLD_UNEXPECTED_BINARY_LABELS")
    use=label.notna() & (label!="")
    d=df.loc[use].reset_index(drop=True)
    labels=label.loc[use].reset_index(drop=True)
    y=(labels==TARGETS[target]["positive"]).astype(int).to_numpy()
    n=len(d)
    ntrain=round(.7*n)
    if n<20 or ntrain<10 or len(set(y.tolist()))!=2 or not ntrain<n:
        raise ValueError("HOLD_TARGET_LABEL_COHORT_INSUFFICIENT")
    ids=d["bird_id"].astype(str).to_numpy()
    if mode=="year_id":
        train=random_year_train_mask(n,ntrain,seed)
    else:
        train=exact_bird_group_train_mask(ids,ntrain,seed)
    train_idx=np.flatnonzero(train)
    test_idx=np.flatnonzero(~train)
    if len(set(y[train_idx].tolist()))!=2:
        raise ValueError("HOLD_TRAINING_CLASS_DEGENERATE")
    features_train,features_test=_predictor_matrices(d,train_idx,test_idx)
    target_offset=0 if target=="HR" else 10000
    model=RandomForestClassifier(
        n_estimators=500,max_features=5,min_samples_leaf=1,
        criterion="gini",bootstrap=True,class_weight=None,
        random_state=int(seed+target_offset),n_jobs=1
    )
    model.fit(features_train,y[train_idx])
    p=model.predict_proba(features_test)[:,list(model.classes_).index(1)]
    train_birds=set(ids[train_idx])
    test_birds=set(ids[test_idx])
    if mode=="bird_id" and (train_birds & test_birds):
        raise ValueError("HOLD_BIRD_ID_SPLIT_HAS_SHARED_BIRD")
    result=_metrics_from_probs(y[test_idx],p,float(y[train_idx].mean()),
                               len(train_idx),len(test_birds),len(train_birds),
                               len(train_birds&test_birds))
    return result

def _summarize_panels(panels):
    import numpy as np
    out=[]
    for target,mode in product(TARGETS,("year_id","bird_id")):
        subset=[p for p in panels if p["target"]==target and p["split_mode"]==mode]
        if len(subset)!=len(SEEDS):
            raise ValueError("MISSING_OR_SUBSTITUTED_FROZEN_SEED_PANEL")
        numeric_fields=[
            "train_n","test_n","train_unique_bird_ids","test_unique_bird_ids",
            "overlapping_bird_ids","test_positive_fraction","test_accuracy",
            "test_balanced_accuracy","test_roc_auc","test_log_loss","test_brier",
            "test_mean_log_score_gain_vs_training_prevalence"
        ]
        stats={}
        for k in numeric_fields:
            values=[float(p[k]) for p in subset if p[k] is not None]
            stats[k]=None if not values else {
                "mean":round(float(np.mean(values)),6),
                "median":round(float(np.median(values)),6),
                "min":round(float(min(values)),6),
                "max":round(float(max(values)),6)
            }
        out.append({
            "target":target,"split_mode":mode,
            "frozen_eight_seeds_reported":len(subset),
            "summary":stats
        })
    diff=[]
    for target in TARGETS:
        a={p["seed"]:p for p in panels if p["target"]==target and p["split_mode"]=="year_id"}
        b={p["seed"]:p for p in panels if p["target"]==target and p["split_mode"]=="bird_id"}
        diff.append({
            "target":target,
            "descriptive_mean_year_minus_bird_log_score_gain":round(sum(
                a[s]["test_mean_log_score_gain_vs_training_prevalence"]-
                b[s]["test_mean_log_score_gain_vs_training_prevalence"] for s in SEEDS)/len(SEEDS),6),
            "descriptive_mean_year_minus_bird_brier":round(sum(
                a[s]["test_brier"]-b[s]["test_brier"] for s in SEEDS)/len(SEEDS),6),
            "not_an_inferential_p_value_or_independent_study_replication":True
        })
    return out,diff

def evaluate_dataframe(df):
    import pandas as pd
    import sklearn
    import numpy as np
    if len(df)!=697 or tuple(x for x in ("year_id","bird_id",*FEATURES,"HR","nest") if x not in df.columns):
        raise ValueError("SOURCE_SCHEMA_OR_FEATURE_COLUMNS_CHANGED")
    if df["year_id"].isna().any() or df["bird_id"].isna().any():
        raise ValueError("MISSING_ANIMAL_OR_SEASON_ID")
    if df["year_id"].nunique()!=697 or df["bird_id"].nunique()!=258:
        raise ValueError("HOLD_RDS_SOURCE_ROSTER_MISMATCH")
    hist=Counter(Counter(df["bird_id"].astype(str)).values())
    if {str(k):hist[k] for k in sorted(hist)}!=HIST_EXPECT:
        raise ValueError("HOLD_RDS_SOURCE_MULTISEASON_HISTOGRAM_MISMATCH")
    panels=[]
    for target in TARGETS:
        for seed in SEEDS:
            for mode in ("year_id","bird_id"):
                result=model_one_panel(df,target,mode,seed)
                panels.append({"target":target,"seed":int(seed),"split_mode":mode,**result})
    summaries,differences=_summarize_panels(panels)
    return {
        "schema_version":1,
        "status":"SWISS_SAME_SOURCE_BIRD_DISJOINT_RF_REFIT_COMPARISON",
        "frozen_contract_sha256":hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "source_prepublication_RDS_Git_blob_SHA1_verified_by_CI":True,
        "verified_RDS_schema_697_seasons_258_bird_ID_strings":True,
        "outcomes_used":["HR","nest"],
        "success_outcome_not_read":True,
        "model":"scikit_learn_500_tree_RF_5_mtry_refit_NOT_exact_2024_ranger",
        "package_versions":{"numpy":np.__version__,"pandas":pd.__version__,"scikit_learn":sklearn.__version__},
        "source_histogram":HIST_EXPECT,
        "eight_precommitted_seeds":list(SEEDS),
        "model_metrics_per_seed_aggregate_only":panels,
        "mode_by_target_summary":summaries,
        "year_minus_bird_split_descriptive_differences":differences,
        "no_event_data_or_real_bird_or_year_IDs_exported":True,
        "not_original_2024_random_split_or_model":True,
        "no_formal_claim_about_original_accuracy_inflation_or_future_group_coverage":True,
        "BOP_original_terminal":"empirical_state_prediction_mixed",
        "redkite_external_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
    }

def run(input_path:Path):
    load_frozen()
    import pandas as pd
    df=pd.read_csv(input_path,dtype={"year_id":"string","bird_id":"string","sex":"string","HR":"string","nest":"string"})
    return evaluate_dataframe(df)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--table",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if args.out.resolve() in (CONTRACT.resolve(),args.table.resolve()):
        raise ValueError("model output cannot overwrite frozen contract or private input")
    try:
        result=run(args.table)
    except (OSError,ValueError,TypeError,RuntimeError) as exc:
        result={
            "schema_version":1,"status":"HOLD_PREPARED_RDS_SOURCE_OR_REFIT",
            "error_type":type(exc).__name__,
            "source_prepublication_RDS_Git_blob_SHA1_verified_by_CI":True,
            "no_event_data_or_real_bird_or_year_IDs_exported":True,
            "redkite_external_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
            "BOP_original_terminal":"empirical_state_prediction_mixed"
        }
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True,allow_nan=False))
    if result["status"]!="SWISS_SAME_SOURCE_BIRD_DISJOINT_RF_REFIT_COMPARISON":
        raise SystemExit("HOLD_PREPARED_SOURCE_OR_COMPARISON: no substitute data or posthoc features")

if __name__=="__main__":
    main()
