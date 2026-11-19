#!/usr/bin/env Rscript
# Swiss 2024 prepared-source, same-test other-year-exposure ranger audit.
# Contract frozen BEFORE any new RDS/label read. Artifact: aggregate metrics
# only, no source animal identifiers, timestamps, features or outcomes.
#
# This uses original NestTool's R ranger probability-forest FAMILY and 34
# predictors, NOT the authors' tuned 2024 model or their saved random split.

predictors <- c(
 "sex","revisits_day","residence_time_day","age_cy",
 "revisits_night","residence_time_night",
 "dist_max_day_to_max_night","median_day_dist_to_max_night",
 "relative_dist_max_day_to_max_night",
 "revisitsSettle","revisitsIncu1","revisitsIncu2",
 "revisitsChick1","revisitsChick2","timeSettle","timeIncu1",
 "timeIncu2","timeChick1","timeChick2",
 "meandayrevisitsBrood","lastvisitDay","maxtimeawayBrood2km",
 "maxtimeawayBrood","tottime_nest",
 "Dist99Chick2","Dist99Settle","Dist99Incu1","Dist99Incu2",
 "Dist99Chick1","MCP95Chick2","MCP95Chick1",
 "MCP95Incu1","MCP95Settle","MCP95Incu2"
)
seeds <- as.integer(20261119:20261134)
hist_frozen <- c("1"=66L,"2"=51L,"3"=62L,"4"=56L,"5"=20L,"6"=2L,"7"=1L)
labels_allowed <- list(HR=c("no","yes"),nest=c("no nest","nest"))
contract_path <- "research/BOP_SWISS_RANGER_PAIRED_OTHER_YEAR_EXPOSURE_V1_CONTRACT.json"

require_true <- function(condition, message="FROZEN_SOURCE_OR_DESIGN_HOLD") {
  if (!isTRUE(condition)) stop(message,call.=FALSE)
}

check_contract <- function() {
  require_true(requireNamespace("jsonlite",quietly=TRUE),"MISSING_JSONLITE")
  c <- jsonlite::read_json(contract_path,simplifyVector=TRUE)
  d<-c$paired_fixed_design; m<-c$fixed_R_ranger_model
  s<-c$source_gate; a<-c$immutable_source; z<-c$inference_limit
  require_true(identical(c$contract_id,"bop-swiss-ranger-same-test-bird-other-year-exposure-v1"))
  require_true(identical(c$freeze_date,"2026-11-19"))
  require_true(a$byte_length==53709803L &&
    identical(a$git_blob_sha1,"fab942c0df8d6f77dc1db2bd2e2717681b9a3632"))
  frozen_hist<-vapply(names(hist_frozen),function(key)
    as.integer(s$exact_h_1_to_7[[key]]),integer(1))
  names(frozen_hist)<-names(hist_frozen)
  require_true(identical(frozen_hist,hist_frozen) &&
    identical(as.character(s$exact_34_predictors),predictors))
  require_true(identical(as.character(s$allowed_response_columns),names(labels_allowed)))
  require_true(s$required_HR_nest_known_binary_labels_for_all_697_seasons &&
    s$success_response_must_never_be_accessed)
  require_true(identical(as.integer(d$seeds),seeds))
  require_true(d$target_n_test_birds_per_seed==50L &&
    d$train_total_seasons_each_arm==488L &&
    d$common_training_seasons_from_all_other_birds==438L &&
    d$control_filler_seasons_from_unused_other_birds==50L &&
    d$exposed_filler_seasons_one_other_year_from_each_test_bird==50L &&
    d$test_seasons_each_arm==50L)
  require_true(d$group_safe_train_has_exactly_zero_bird_overlap_with_test &&
    d$exposed_train_has_exactly_50_bird_overlap_with_test &&
    d$same_test_year_ids_exactly_in_both_arms &&
    d$no_pretense_that_other_season_is_chronologically_earlier)
  require_true(m$n_trees==500L && m$mtry==5L &&
    m$minimum_terminal_node_size==10L && m$replace && m$probability &&
    m$sample_fraction==1 && identical(m$split_rule,"gini") &&
    identical(m$importance,"none") && m$num_threads==1L &&
    m$seed_offset_for_nest==10000L && m$test_logloss_prob_clip==0.000001)
  require_true(z$do_not_claim_pure_causal_leakage_effect &&
    z$repeated_splits_not_independent_studies &&
    identical(z$prior_ODSP_BOP,"empirical_state_prediction_mixed") &&
    identical(z$redkite_biological_external,
      "HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"))
  invisible(TRUE)
}

# IDs and predictors are inspected transiently; no real source identifiers are
# included in returned artifacts or logs.
check_schema <- function(dat) {
  require_true(is.data.frame(dat) && nrow(dat)==697L)
  require_true(all(c("bird_id","year_id",predictors,"HR","nest") %in% names(dat)))
  yr<-as.character(dat[["year_id"]])
  bird<-as.character(dat[["bird_id"]])
  require_true(!anyNA(yr) && !anyNA(bird) &&
    all(nzchar(yr)) && all(nzchar(bird)) &&
    anyDuplicated(yr)==0L && length(unique(bird))==258L)
  observed<-table(table(bird))
  actual<-setNames(as.integer(observed),names(observed))
  require_true(identical(actual,hist_frozen))
  invisible(list(bird=bird,year=yr))
}

# This split uses ONLY bird identity strings and their year counts, never
# source predictor values or biological response labels.
make_paired_split <- function(bird,seed) {
  require_true(length(bird)==697L)
  all_counts<-table(bird)
  exactly_two<-sort(names(all_counts)[as.integer(all_counts)==2L])
  require_true(length(exactly_two)==51L)
  RNGkind("Mersenne-Twister","Inversion","Rejection")
  set.seed(as.integer(seed))
  selected<-sample(exactly_two,50L,replace=FALSE)
  test<-integer(50)
  exposed_earlier_or_later<-integer(50)
  for (i in seq_along(selected)) {
    idx<-which(bird==selected[[i]])
    require_true(length(idx)==2L)
    test[[i]]<-sample(idx,1L)
    exposed_earlier_or_later[[i]]<-idx[idx!=test[[i]]]
  }
  outsiders<-which(!(bird %in% selected))
  require_true(length(outsiders)==597L)
  common<-sample(outsiders,438L,replace=FALSE)
  control_pool<-setdiff(outsiders,common)
  require_true(length(control_pool)==159L)
  control_filler<-sample(control_pool,50L,replace=FALSE)
  disjoint_train<-c(common,control_filler)
  exposed_train<-c(common,exposed_earlier_or_later)
  require_true(length(test)==50L && length(unique(test))==50L &&
    length(unique(disjoint_train))==488L &&
    length(unique(exposed_train))==488L &&
    length(intersect(test,disjoint_train))==0L &&
    length(intersect(test,exposed_train))==0L &&
    length(intersect(disjoint_train,exposed_train))==438L)
  # Every test bird occurs once in test; none in clean control train;
  # the exposed training arm includes its other-year episode.
  test_birds<-unique(bird[test])
  require_true(length(test_birds)==50L &&
    length(intersect(test_birds,unique(bird[disjoint_train])))==0L &&
    length(intersect(test_birds,unique(bird[exposed_train])))==50L)
  list(
    test=test,
    disjoint_train=disjoint_train,
    exposed_train=exposed_train,
    test_bird_IDs=test_birds,
    test_n=50L,
    train_n=488L,
    common_train_n=438L,
    clean_bird_overlap=0L,
    exposed_bird_overlap=50L
  )
}

# Train-only imputation; exactly the same test rows on both sides of the
# comparison; any changed test imputation is induced only by training.
transform_predictors <- function(dat,train_idx,test_idx) {
  tr<-dat[train_idx,predictors,drop=FALSE]
  te<-dat[test_idx,predictors,drop=FALSE]
  for (feature in predictors) {
    if (feature=="sex") {
      x<-tolower(trimws(as.character(tr[[feature]])))
      y<-tolower(trimws(as.character(te[[feature]])))
      x[is.na(x)|x==""]<-NA_character_
      y[is.na(y)|y==""]<-NA_character_
      allowed<-c("m","f")
      require_true(all(x[!is.na(x)] %in% allowed) &&
        all(y[!is.na(y)] %in% allowed),"UNEXPECTED_SEX_CATEGORY")
      present<-table(factor(x,levels=allowed))
      replacement<-allowed[[which.max(present)]]
      x[is.na(x)]<-replacement
      y[is.na(y)]<-replacement
      tr[[feature]]<-factor(x,levels=allowed)
      te[[feature]]<-factor(y,levels=allowed)
    } else {
      xraw<-trimws(as.character(tr[[feature]]))
      yraw<-trimws(as.character(te[[feature]]))
      check_numeric<-function(token) {
        known<-!is.na(token) & nzchar(token) &
          !(tolower(token) %in% c("na","nan","inf","-inf"))
        numeric_value<-suppressWarnings(as.numeric(token))
        require_true(!any(known & is.na(numeric_value)),
                     "UNEXPECTED_NUMERIC_SOURCE_COLUMN")
        numeric_value[!is.finite(numeric_value)]<-NA_real_
        numeric_value
      }
      a<-check_numeric(xraw)
      b<-check_numeric(yraw)
      present<-a[!is.na(a)]
      fill<-if (length(present)>0L) median(present) else 0
      a[is.na(a)]<-fill
      b[is.na(b)]<-fill
      tr[[feature]]<-a
      te[[feature]]<-b
    }
  }
  require_true(ncol(tr)==34L && ncol(te)==34L &&
    !anyNA(tr) && !anyNA(te),"TRAIN_ONLY_IMPUTATION_FAILURE")
  list(train=tr,test=te)
}

binary_targets <- function(dat) {
  labels<-list()
  for (target in names(labels_allowed)) {
    l<-tolower(trimws(as.character(dat[[target]])))
    require_true(length(l)==697L && !anyNA(l) &&
      all(l %in% labels_allowed[[target]]) &&
      all(c(TRUE,FALSE) %in% (l==labels_allowed[[target]][[2]])),
      "SOURCE_TARGET_LABELS_NOT_FROZEN_BINARY")
    labels[[target]]<-as.integer(l==labels_allowed[[target]][[2]])
  }
  labels
}

evaluate_metrics <- function(ytest,prob,train_prior) {
  require_true(length(prob)==length(ytest) && length(prob)>0L &&
    all(is.finite(prob)) && all(prob>=0 & prob<=1))
  p<-pmin(pmax(as.numeric(prob),1e-6),1-1e-6)
  ref<-min(max(mean(train_prior),1e-6),1-1e-6)
  y<-as.integer(ytest)
  require_true(all(y %in% 0:1))
  loglike<-ifelse(y==1L,log(p),log(1-p))
  ref_like<-ifelse(y==1L,log(ref),log(1-ref))
  classification<-as.integer(p>=.5)
  npos<-sum(y==1L); nneg<-sum(y==0L)
  auc<-if (npos>0L && nneg>0L) {
    (sum(rank(p,ties.method="average")[y==1L])-npos*(npos+1)/2)/(npos*nneg)
  } else NA_real_
  bacc<-if (npos>0L && nneg>0L)
    .5*(sum(classification[y==1L]==1L)/npos +
          sum(classification[y==0L]==0L)/nneg)
    else NA_real_
  list(
    test_accuracy=round(mean(classification==y),6),
    test_balanced_accuracy=round(bacc,6),
    test_auc=round(auc,6),
    test_log_loss=round(-mean(loglike),6),
    test_brier=round(mean((p-y)^2),6),
    test_mean_log_score_gain_vs_train_prevalence=round(mean(loglike-ref_like),6),
    test_positive_fraction=round(mean(y),6),
    train_positive_fraction=round(mean(train_prior),6)
  )
}

# Scikit-learn is deliberately NOT used here. Both models use the original
# NestTool's ranger probability-forest algorithm family, but fixed 500 trees,
# mtry=5, min.node.size=10 (not authors' OOB tuned hyperparameters).
fit_one <- function(dat,labels,training,test,target,seed) {
  require_true(requireNamespace("ranger",quietly=TRUE),"MISSING_RANGER")
  cov<-transform_predictors(dat,training,test)
  positives<-labels[[target]]
  labels<-factor(ifelse(positives[training]==1L,"yes","no"),levels=c("no","yes"))
  train<-cov$train
  train[[".outcome"]]<-labels
  fit<-ranger::ranger(
    dependent.variable.name=".outcome",
    data=train,
    probability=TRUE,
    num.trees=500L,
    mtry=5L,
    min.node.size=10L,
    replace=TRUE,
    sample.fraction=1,
    splitrule="gini",
    importance="none",
    num.threads=1L,
    seed=as.integer(seed+if (target=="nest") 10000L else 0L)
  )
  p<-ranger::predict(fit,data=cov$test,num.threads=1L)$predictions[,"yes"]
  evaluate_metrics(positives[test],p,positives[training])
}

safe_aggregate <- function(dat) {
  check_contract()
  ids<-check_schema(dat)
  targets<-binary_targets(dat)
  panels<-list()
  paired<-list()
  panel_index<-1L
  pair_index<-1L
  for (seed in seeds) {
    split<-make_paired_split(ids$bird,seed)
    for (target in names(labels_allowed)) {
      safe<-fit_one(dat,targets,split$disjoint_train,split$test,target,seed)
      exposed<-fit_one(dat,targets,split$exposed_train,split$test,target,seed)
      for (mode in c("disjoint_other_birds","same_bird_other_year_exposure")) {
        scores<-if (mode=="disjoint_other_birds") safe else exposed
        panels[[panel_index]]<-c(
          list(target=target,seed=as.integer(seed),mode=mode,
               training_seasons=488L,test_seasons=50L,
               test_unique_bird_ID_strings=50L,
               train_and_test_bird_ID_overlap=if(mode=="disjoint_other_birds")0L else 50L,
               training_rows_common=438L),
          scores
        )
        panel_index<-panel_index+1L
      }
      paired[[pair_index]]<-list(
        target=target,seed=as.integer(seed),
        SAME_TEST_50_ROWS=TRUE,
        exposed_minus_disjoint_log_score_gain=round(
          exposed$test_mean_log_score_gain_vs_train_prevalence-
          safe$test_mean_log_score_gain_vs_train_prevalence,6),
        exposed_minus_disjoint_test_log_loss=round(
          exposed$test_log_loss-safe$test_log_loss,6),
        exposed_minus_disjoint_brier=round(
          exposed$test_brier-safe$test_brier,6),
        exposed_minus_disjoint_accuracy=round(
          exposed$test_accuracy-safe$test_accuracy,6),
        # Deliberately no p-values: 16 source-resampling splits are correlated.
        not_independent_study_replications=TRUE
      )
      pair_index<-pair_index+1L
    }
  }
  require_true(length(panels)==64L && length(paired)==32L)
  summarise_scalar<-function(vals) {
    vals<-vals[is.finite(vals)]
    if (!length(vals)) return(NULL)
    list(mean=round(mean(vals),6),median=round(median(vals),6),
         min=round(min(vals),6),max=round(max(vals),6))
  }
  metrics<-c("test_accuracy","test_balanced_accuracy","test_auc",
    "test_log_loss","test_brier","test_mean_log_score_gain_vs_train_prevalence",
    "test_positive_fraction","train_positive_fraction")
  summaries<-list()
  for (target in names(labels_allowed)) {
    for (mode in c("disjoint_other_birds","same_bird_other_year_exposure")) {
      group<-Filter(function(x) identical(x$target,target) &&
                           identical(x$mode,mode),panels)
      require_true(length(group)==16L)
      summaries[[length(summaries)+1L]]<-list(
        target=target,mode=mode,
        n_precommitted_seeds=16L,
        test_rows_per_seed=50L,train_rows_per_seed=488L,
        train_and_test_bird_overlap=if (mode=="disjoint_other_birds")0L else 50L,
        all_metrics=setNames(lapply(metrics,function(k)
          summarise_scalar(vapply(group,function(x)
            as.numeric(x[[k]]),numeric(1)))),metrics)
      )
    }
  }
  pair_summaries<-lapply(names(labels_allowed),function(target){
    group<-Filter(function(x) identical(x$target,target),paired)
    keys<-c("exposed_minus_disjoint_log_score_gain",
            "exposed_minus_disjoint_test_log_loss",
            "exposed_minus_disjoint_brier",
            "exposed_minus_disjoint_accuracy")
    list(target=target,paired_identical_test_rows_each_seed=TRUE,
         paired_descriptive_differences=setNames(lapply(keys,function(k)
           summarise_scalar(vapply(group,function(x)
             as.numeric(x[[k]]),numeric(1)))),keys),
         no_formal_p_value=TRUE)
  })
  list(
    schema_version=1L,
    status="PAIRED_SAME_TEST_2024_RANGER_SOURCE_REFIT",
    source_git_blob_SHA1_verified_in_CI=TRUE,
    model_family="R_ranger_fixed_500_trees_mtry_5_node_10_not_original_tuned_RF",
    R_version=R.version.string,
    ranger_version=as.character(utils::packageVersion("ranger")),
    jsonlite_version=as.character(utils::packageVersion("jsonlite")),
    source_seasons=697L,source_bird_ID_strings=258L,
    two_season_bird_ID_pool=51L,test_birds_per_seed=50L,
    train_seasons_per_mode=488L,test_seasons_per_mode=50L,
    training_rows_common_in_both_modes=438L,
    test_rows_identical_within_seed_between_modes=TRUE,
    other_year_of_test_bird_chronology_not_assumed=TRUE,
    precommitted_seeds=as.integer(seeds),
    panel_count=length(panels),paired_comparisons_count=length(paired),
    aggregate_score_panels=panels,
    aggregate_pairwise_differences=paired,
    source_summary_by_target_and_mode=summaries,
    paired_difference_summary_by_target=pair_summaries,
    no_single_row_predictions_animal_IDs_or_labels_exported=TRUE,
    no_2024_original_model_reproduction_or_accuracy_bias_causality_claim=TRUE,
    original_BOP_terminal="empirical_state_prediction_mixed",
    redkite_external_terminal="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
  )
}

synthetic_known_truth <- function() {
  # exactly the original *histogram*, with entirely artificial individuals;
  # tests splitting and real ranger fitting, never reading a source file.
  bird<-character()
  for (k in seq_len(7)) {
    for (i in seq_len(hist_frozen[[as.character(k)]]))
      bird<-c(bird,rep(sprintf("synthetic-%i-%i",k,i),k))
  }
  require_true(length(bird)==697L && length(unique(bird))==258L)
  idx<-seq_along(bird)
  dat<-data.frame(bird_id=bird,year_id=sprintf("fake-year-%i",idx))
  for (feature in predictors) {
    dat[[feature]]<-if(feature=="sex")ifelse(idx%%2==0,"m","f") else
      (sin(idx/7)+idx/699 + which(predictors==feature)/17)
  }
  dat[["HR"]]<-ifelse(idx%%3==0,"yes","no")
  dat[["nest"]]<-ifelse(idx%%4==0,"nest","no nest")
  check_schema(dat)
  a<-make_paired_split(dat$bird_id,seeds[[1]])
  b<-make_paired_split(dat$bird_id,seeds[[1]])
  require_true(identical(a$test,b$test) &&
    identical(a$disjoint_train,b$disjoint_train) &&
    identical(a$exposed_train,b$exposed_train) &&
    a$test_n==50L && a$train_n==488L && a$common_train_n==438L &&
    a$clean_bird_overlap==0L && a$exposed_bird_overlap==50L)
  for (seed in seeds) {
    spl<-make_paired_split(dat$bird_id,seed)
    require_true(length(spl$test)==50L &&
      length(intersect(dat$bird_id[spl$disjoint_train],
                       dat$bird_id[spl$test]))==0L &&
      length(intersect(dat$bird_id[spl$exposed_train],
                       dat$bird_id[spl$test]))==50L)
  }
  y<-binary_targets(dat)
  r1<-fit_one(dat,y,a$disjoint_train,a$test,"HR",seeds[[1]])
  r2<-fit_one(dat,y,a$exposed_train,a$test,"HR",seeds[[1]])
  require_true(all(is.finite(unlist(r1))) && all(is.finite(unlist(r2))) &&
    r1$test_accuracy>=0 && r1$test_accuracy<=1 &&
    r2$test_brier>=0 && r2$test_brier<=1)
  cat("SYNTHETIC_SOURCE_FREE_TEST_PASSED\n")
}

main <- function(args) {
  check_contract()
  if (length(args)==1L && identical(args[[1]],"--self-test")) {
    synthetic_known_truth()
    return(invisible(TRUE))
  }
  require_true(length(args)==2L,"USAGE_RANGER_SOURCE_RDS_OUT_JSON")
  file<-args[[1]]
  dest<-args[[2]]
  source_success<-FALSE
  tryCatch({
    require_true(requireNamespace("ranger",quietly=TRUE),"RANGER_NOT_INSTALLED")
    require_true(file.exists(file) && file.info(file)$size==53709803,
                 "SOURCE_RDS_MISSING_OR_WRONG_SIZE")
    dat0<-readRDS(file)
    require_true(is.list(dat0) && is.data.frame(dat0[["summary"]]),
                 "SOURCE_SUMMARY_INVALID")
    dat<-dat0[["summary"]]
    rm(dat0)
    # SOURCE HAS PASSED THE OUTCOME-BLIND PRE-STEP; exact files checked by CI
    # before readRDS. Never index or export original 'success'.
    result<-safe_aggregate(dat)
    jsonlite::write_json(result,dest,auto_unbox=TRUE,pretty=TRUE,na="null",digits=NA)
    cat("PAIRED_SAME_TEST_2024_RANGER_SOURCE_REFIT_AGGREGATES_WRITTEN\n")
    source_success<-TRUE
  },error=function(e) {
    jsonlite::write_json(list(
      schema_version=1L,status="HOLD_PAIRED_SOURCE_RANGER_SAME_TEST",
      error_type="R_SOURCE_MODEL_GATE_OR_FIT",
      no_individual_input_features_or_labels_emitted=TRUE,
      original_BOP_terminal="empirical_state_prediction_mixed",
      redkite_external_terminal="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
    ),dest,auto_unbox=TRUE,pretty=TRUE,na="null")
  })
  if (!source_success) quit(save="no",status=1L)
  invisible(TRUE)
}

if (sys.nframe()==0L) {
  args<-commandArgs(trailingOnly=TRUE)
  main(args)
}
