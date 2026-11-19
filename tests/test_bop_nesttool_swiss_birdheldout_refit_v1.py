"""Known-truth synthetic tests for predeclared Swiss bird-disjoint RF comparison.

No real biological source or label is read by the tests.
"""
from __future__ import annotations
from collections import Counter
import json
import pytest

# The general ODSP scientific/governance CI intentionally has no pandas/numpy/
# scikit-learn dependencies. These optional RF tests are mandatory in the
# dedicated bird-heldout workflow (which installs all three), while the
# dependency-light core/governance lanes should skip them at collection.
np=pytest.importorskip("numpy",reason="optional RF evaluation requires numpy")
pd=pytest.importorskip("pandas",reason="optional RF evaluation requires pandas")
pytest.importorskip("sklearn",reason="optional RF evaluation requires scikit-learn")

from scripts.bop_nesttool_swiss_birdheldout_refit_v1 import (
    CONTRACT,FEATURES,HIST_EXPECT,SEEDS,TARGETS,load_frozen,
    random_year_train_mask,exact_bird_group_train_mask,
    _predictor_matrices,model_one_panel,_summarize_panels,
)

def fake_df(nbird=20,nseasons=2):
    rows=[]
    for i in range(nbird):
        for y in range(nseasons):
            row={"year_id":f"year{i}_{y}","bird_id":f"animal{i}",
                 "HR":"yes" if (i+y)%2==0 else "no",
                 "nest":"nest" if (i+y)%3!=0 else "no nest"}
            for j,feat in enumerate(FEATURES):
                row[feat]=("m" if i%2 else "f") if feat=="sex" else float(i+j+y*.5)
            rows.append(row)
    return pd.DataFrame(rows)

def test_freeze_and_predictor_contract():
    c=load_frozen()
    assert c["source"]["source_bytes"]==53709803
    assert c["source"]["git_blob_sha1"]=="fab942c0df8d6f77dc1db2bd2e2717681b9a3632"
    assert c["source"]["historical_usage_source_line"]==103
    assert c["source_schema_gate"]["required_exact_group_histogram_1_to_7"]==HIST_EXPECT
    assert len(FEATURES)==34
    assert c["modeling"]["seeds"]==list(SEEDS)
    assert set(c["modeling"]["allowed_response_variables"])==set(TARGETS)
    assert c["modeling"]["do_not_export_per_year_predicted_probs_or_actual_labels_or_animal_IDs"] is True
    assert c["science_limits"]["historic_ODSP"]=="empirical_state_prediction_mixed"

def test_group_subset_sum_is_exact_and_no_bird_id_overlap():
    birds=["bird1"]*7+["bird2"]*6+["bird3"]*5+["bird4"]*4+["bird5"]*3+["bird6"]*2+["bird7"]*1
    for seed in SEEDS:
        mask=exact_bird_group_train_mask(birds,18,seed)
        assert mask.sum()==18
        assert not(set(np.array(birds)[mask])&set(np.array(birds)[~mask]))
    with pytest.raises(ValueError,match="UNMATCHABLE"):
        exact_bird_group_train_mask(["a"]*3+["b"]*3,5,20261119)

def test_random_year_split_is_exact_count_not_bird_disjoint():
    mask=random_year_train_mask(697,488,20261119)
    assert mask.sum()==488 and (~mask).sum()==209
    assert np.array_equal(mask,random_year_train_mask(697,488,20261119))
    assert not np.array_equal(mask,random_year_train_mask(697,488,20261120))

def test_train_only_imputation_does_not_use_test_feature_median():
    df=fake_df(nbird=10,nseasons=2)
    feat="revisits_day"
    df.loc[0,feat]=np.nan
    df.loc[5,feat]=1e9
    idx_train=np.array([0,1,2,3])
    idx_test=np.array([4,5,6,7])
    x,z=_predictor_matrices(df,idx_train,idx_test)
    fidx=FEATURES.index(feat)
    assert x.shape==(4,34) and z.shape==(4,34)
    assert x[0,fidx]==pytest.approx(np.median([float(df.loc[i,feat]) for i in (1,2,3)]))
    assert z[1,fidx]==1e9
    assert np.isfinite(x).all() and np.isfinite(z).all()

def test_small_synthetic_two_split_modes_return_only_aggregate_metrics():
    df=fake_df(nbird=24,nseasons=2)
    for target in TARGETS:
        for mode in ("year_id","bird_id"):
            r=model_one_panel(df,target,mode,20261119)
            assert r["train_n"]==34
            assert r["test_n"]==14
            assert 0<=r["test_brier"]<=1
            assert r["test_log_loss"]>=0
            assert r["test_accuracy"]>=0
            assert r["overlapping_bird_ids"]==0 if mode=="bird_id" else r["overlapping_bird_ids"]>=0
            text=json.dumps(r)
            assert "bird1" not in text and "year0" not in text
            assert "predicted_class_by_event" not in text

def test_nonbinary_label_is_HOLD_without_redefining_target():
    df=fake_df()
    df.loc[0,"HR"]="undocumented third outcome"
    with pytest.raises(ValueError,match="UNEXPECTED_BINARY_LABELS"):
        model_one_panel(df,"HR","bird_id",20261119)

def test_unknown_sex_category_is_HOLD():
    df=fake_df()
    df.loc[0,"sex"]="undocumented"
    with pytest.raises(ValueError,match="UNEXPECTED_SEX_CATEGORY"):
        model_one_panel(df,"HR","bird_id",20261119)

def test_metric_summary_rejects_missing_frozen_seed_not_claimed_statistics():
    panels=[]
    r={"train_n":34,"test_n":14,"train_unique_bird_ids":20,
       "test_unique_bird_ids":10,"overlapping_bird_ids":0,
       "test_positive_fraction":.5,"test_accuracy":.7,
       "test_balanced_accuracy":.7,"test_roc_auc":.8,
       "test_log_loss":.6,"test_brier":.2,
       "test_mean_log_score_gain_vs_training_prevalence":.05}
    for target in TARGETS:
        for seed in SEEDS:
            for mode in ("year_id","bird_id"):
                panels.append({"target":target,"seed":seed,"split_mode":mode,**r})
    summary,diff=_summarize_panels(panels)
    assert len(summary)==4 and len(diff)==2
    assert all(q["frozen_eight_seeds_reported"]==8 for q in summary)
    assert all(q["descriptive_mean_year_minus_bird_brier"]==0 for q in diff)
    with pytest.raises(ValueError,match="MISSING_OR_SUBSTITUTED"):
        _summarize_panels(panels[:-1])
