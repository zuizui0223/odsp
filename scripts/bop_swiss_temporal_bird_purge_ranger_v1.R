#!/usr/bin/env Rscript
# Retrospective Swiss source: *global* forward-year evaluation with/without
# biological bird-ID purge. 2024 source labels are ALREADY seen in earlier PRs.
# Source/schema/algorithm/cutoffs were frozen BEFORE this new RDS access.
# Neither per-bird labels nor predictions/IDs are exported.
source("scripts/bop_swiss_ranger_focal_prior_year_v1.R",local=FALSE)
temporal_contract<-"research/BOP_SWISS_TEMPORAL_BIRD_PURGE_V1_CONTRACT.json"
frozen_cutoffs<-c(2020L,2021L,2022L)
frozen_model_seeds<-as.integer(20261221:20261228)
frozen_modes<-c("full_forward","bird_purged_forward")
frozen_targets<-c("HR","nest")

check_temporal_contract<-function() {
  # Reuse the exact original-family ranger settings, source schema,
  # input predictors and train-only preprocessing from merged PR #297.
  check_contract()
  require_true(requireNamespace("jsonlite",quietly=TRUE))
  c<-jsonlite::read_json(temporal_contract,simplifyVector=TRUE)
  d<-c$design; m<-c$model; g<-c$gate; s<-c$safety; t<-c$terminals
  require_true(identical(c$contract_id,
    "bop-swiss-temporal-forward-bird-purged-ranger-v1") &&
    identical(c$freeze_date,"2026-11-20"))
  require_true(identical(as.integer(d$cutoffs),frozen_cutoffs) &&
    d$primary_cutoff==2021L &&
    identical(as.integer(m$random_model_seeds),frozen_model_seeds) &&
    identical(as.character(m$modes),frozen_modes) &&
    identical(as.character(m$only_targets),frozen_targets))
  require_true(g$rows==697L && g$unique_bird_id_strings==258L &&
    g$minimum_year==2016L && g$maximum_year==2022L &&
    g$outcome_value_unread_until_source_gate_passed)
  hist<-vapply(names(hist_frozen),function(k)
    as.integer(g$source_multiseason_histogram[[k]]),integer(1))
  names(hist)<-names(hist_frozen)
  require_true(identical(hist,hist_frozen))
  require_true(d$all_cutoffs_reported_even_if_infeasible &&
    d$full_forward_train_test_season_row_disjoint &&
    d$purged_forward_bird_id_disjoint &&
    d$all_training_rows_strictly_earlier_than_all_test_rows &&
    d$identical_postcutoff_test_rows_both_models)
  require_true(d$minimum_train_seasons==60L && d$minimum_test_seasons==20L &&
    d$minimum_train_bird_id_strings==20L && d$minimum_test_bird_id_strings==10L &&
    d$minimum_each_class_train==5L && d$minimum_each_class_test==3L)
  require_true(m$n_trees==500L && m$mtry==5L && m$min_node_size==10L &&
    m$probability && m$max_total_models==96L &&
    m$different_cutoff_model_seed_offset==10000L &&
    m$different_target_model_seed_offset==20000L &&
    m$train_only_predictor_imputation &&
    m$no_hyperparameter_tuning_using_test_labels)
  require_true(s$source_full_size_and_git_blob_must_match_before_readRDS &&
    s$source_year_schema_gate_outcome_blind &&
    s$no_one_sided_unseen_future_individual_conformal_certificate)
  require_true(identical(t$original_BOP,"empirical_state_prediction_mixed") &&
    identical(t$external_redkite,
      "HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"))
  invisible(c)
}

forward_purge_indices<-function(bird,years,cutoff) {
  require_true(length(bird)==697L && length(years)==697L &&
    cutoff %in% frozen_cutoffs && all(is.finite(years)))
  test<-which(years>=cutoff)
  full_train<-which(years<cutoff)
  test_bird<-unique(bird[test])
  purged_train<-full_train[!(bird[full_train] %in% test_bird)]
  require_true(length(intersect(test,full_train))==0L &&
    length(intersect(test,purged_train))==0L &&
    length(intersect(unique(bird[purged_train]),test_bird))==0L)
  if(length(full_train)>0L && length(test)>0L)
    require_true(max(years[full_train])<min(years[test]))
  list(
    cutoff=cutoff,
    test=test,
    full_forward=full_train,
    bird_purged_forward=purged_train,
    sample_counts=list(
      cutoff=cutoff,
      full_forward_train_seasons=length(full_train),
      bird_purged_train_seasons=length(purged_train),
      test_seasons=length(test),
      full_train_unique_birds=length(unique(bird[full_train])),
      purged_train_unique_birds=length(unique(bird[purged_train])),
      test_unique_birds=length(test_bird),
      full_forward_train_test_bird_overlap=length(intersect(
        unique(bird[full_train]),test_bird)),
      purged_forward_train_test_bird_overlap=0L,
      identical_postcutoff_test_rows_for_both_modes=TRUE,
      whole_study_train_years_earlier_than_all_test_years=TRUE
    )
  )
}

count_gate<-function(split,mode,c) {
  ntrain<-length(split[[mode]])
  ntest<-length(split$test)
  bird<-c
  list(
    passes=ntrain>=60L && ntest>=20L &&
      length(unique(bird[split[[mode]]]))>=20L &&
      length(unique(bird[split$test]))>=10L,
    train=ntrain,test=ntest
  )
}

label_gate<-function(y,train,test) {
  a<-tabulate(as.integer(y[train])+1L,nbins=2L)
  b<-tabulate(as.integer(y[test])+1L,nbins=2L)
  length(train)>=60L && length(test)>=20L &&
    all(a>=5L) && all(b>=3L)
}

panel_summary<-function(items,target,mode,cutoff) {
  chosen<-Filter(function(x)
    identical(x$target,target) && identical(x$mode,mode) &&
    identical(x$cutoff,cutoff) && identical(x$status,"SCORED"),items)
  if(length(chosen)!=8L)
    return(list(target=target,mode=mode,cutoff=cutoff,status="HOLD_INFEASIBLE_COHORT_OR_CLASS",
      n_models=length(chosen),metric_means=NULL))
  metrics<-c("test_accuracy","test_balanced_accuracy","test_auc",
    "test_log_loss","test_brier",
    "test_mean_log_score_gain_vs_train_prevalence",
    "test_positive_fraction","train_positive_fraction")
  vals<-lapply(metrics,function(metric){
    a<-vapply(chosen,function(z)as.numeric(z[[metric]]),numeric(1))
    a<-a[is.finite(a)]
    if(!length(a))return(NULL)
    list(mean=round(mean(a),6),min=round(min(a),6),
      median=round(median(a),6),max=round(max(a),6))
  })
  names(vals)<-metrics
  list(target=target,mode=mode,cutoff=cutoff,status="SCORED",
       n_models=8L,metric_summary=vals)
}

run_source_experiment<-function(dat) {
  c<-check_temporal_contract()
  ids<-check_schema(dat)
  years<-parse_focal_calendar_years(dat)
  require_true(min(years)==2016L && max(years)==2022L,
               "SOURCE_YEAR_RANGE_NOT_FROZEN")
  splits<-lapply(frozen_cutoffs,function(k)
    forward_purge_indices(ids$bird,years,k))
  # IDs and year bounds validated ABOVE, before outcome *value* reads.
  y<-binary_targets(dat)
  source_panels<-list()
  counter<-1L
  for(split in splits) {
    for(target in frozen_targets) {
      for(mode in frozen_modes) {
        train<-split[[mode]]
        test<-split$test
        ntrain_birds<-length(unique(ids$bird[train]))
        ntest_birds<-length(unique(ids$bird[test]))
        feasible<-count_gate(split,mode,ids$bird)$passes &&
          label_gate(y[[target]],train,test)
        if(!feasible) {
          source_panels[[counter]]<-list(
            cutoff=split$cutoff,target=target,mode=mode,
            status="HOLD_INFEASIBLE_COHORT_OR_CLASS",
            train_seasons=length(train),test_seasons=length(test),
            train_bird_ID_strings=ntrain_birds,
            test_bird_ID_strings=ntest_birds,
            train_test_bird_overlap=if(mode=="bird_purged_forward")0L else
              split$sample_counts$full_forward_train_test_bird_overlap,
            source_class_values_not_exported=TRUE
          )
          counter<-counter+1L
          next
        }
        for(seed in frozen_model_seeds) {
          # fit_one() is the previously audited R ranger implementation:
          # seed input and 10000 extra for nesting target. Add one more 10000
          # for nesting to make the total target offset 20000 (frozen plan).
          effective_seed=as.integer(seed+
            10000L*(split$cutoff-2020L)+
            if(target=="nest")10000L else 0L)
          result<-fit_one(dat,y,train,test,target,effective_seed)
          source_panels[[counter]]<-c(list(
            cutoff=split$cutoff,target=target,mode=mode,
            seed=as.integer(seed),status="SCORED",
            train_seasons=length(train),test_seasons=length(test),
            train_bird_ID_strings=ntrain_birds,
            test_bird_ID_strings=ntest_birds,
            train_test_bird_overlap=if(mode=="bird_purged_forward")0L else
              split$sample_counts$full_forward_train_test_bird_overlap,
            global_train_years_earlier_than_test_years=TRUE
          ),result)
          counter<-counter+1L
        }
      }
    }
  }
  all_summaries<-list()
  for(cutoff in frozen_cutoffs)
    for(target in frozen_targets)
      for(mode in frozen_modes)
        all_summaries[[length(all_summaries)+1L]]<-
          panel_summary(source_panels,target,mode,cutoff)
  prior<-nextPrimary<-Filter(function(x)
    x$cutoff==2021L && x$target=="HR" &&
      x$mode=="bird_purged_forward",all_summaries)
  require_true(length(nextPrimary)==1L)
  overall_status<-if(nextPrimary[[1]]$status=="SCORED")
    "RETROSPECTIVE_SWISS_CALENDAR_FORWARD_BIRD_PURGED_SOURCE_REFIT" else
    "HOLD_SOURCE_YEAR_BIRD_FORWARD_ADMISSION_OR_CLASS_SUPPORT"
  list(
    schema_version=1L,
    status=overall_status,
    retrospective_same_prepared_Swiss_source_not_new_data=TRUE,
    previous_source_HR_nest_labels_already_accessed=TRUE,
    source_prepublication_RDS_git_hash_verified_in_CI=TRUE,
    source_original_697_year_IDs_258_bird_IDs_verified=TRUE,
    source_calendar_years_range=c(min(years),max(years)),
    primary_temporal_cutoff=2021L,
    all_predeclared_cutoffs=as.integer(frozen_cutoffs),
    two_training_modes=as.character(frozen_modes),
    model_family="R_ranger_fixed_500_trees_mtry_5_node_10_not_tuned_original_2024",
    ranger_version=as.character(utils::packageVersion("ranger")),
    R_version=R.version.string,
    original_34_predictors=length(predictors),
    all_source_cutoff_cohort_counts=lapply(splits,function(x)x$sample_counts),
    all_cutoff_response_model_summaries=all_summaries,
    per_seed_aggregate_only_model_panels=source_panels,
    n_successful_models=sum(vapply(source_panels,
      function(x)identical(x$status,"SCORED"),logical(1))),
    n_infeasible_cutoff_target_mode_panels=sum(vapply(source_panels,
      function(x)identical(x$status,"HOLD_INFEASIBLE_COHORT_OR_CLASS"),logical(1))),
    source_model_seed_indices_as_frozen=as.integer(frozen_model_seeds),
    no_raw_individual_source_IDs_or_past_future_annual_records_exported=TRUE,
    globally_forward_years_for_training_and_test=TRUE,
    purged_arm_zero_bird_ID_overlap=TRUE,
    no_external_country_or_untouched_future_validation_claim=TRUE,
    prior_vs_purged_training_samples_not_equal_size=TRUE,
    original_BOP_terminal="empirical_state_prediction_mixed",
    redkite_external_terminal="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
  )
}

synthetic_test<-function() {
  # Synthetic source fake 697 year rows exactly matching 2024 aggregate
  # histogram, with calendar years 2016..2022 and both known synthetic labels.
  bird<-character();years<-integer()
  for(k in 1:7) {
    for(i in seq_len(hist_frozen[[as.character(k)]])) {
      start<-2016L + (i-1L) %% (8L-k)
      for(j in seq_len(k)) {
        bird<-c(bird,sprintf("fake-source-bird-%i-%i",k,i))
        years<-c(years,start+j-1L)
      }
    }
  }
  require_true(length(bird)==697L && length(unique(bird))==258L)
  n<-seq_along(bird)
  dat<-data.frame(year_id=paste0(years,"_fake_",n),bird_id=bird,
                  year=years)
  for(feature in predictors)
    dat[[feature]]<-if(feature=="sex")ifelse(n%%2,"m","f") else
      sin(n/13)+n/697+which(predictors==feature)/11
  dat$HR<-ifelse(n%%5==0,"yes","no")
  dat$nest<-ifelse(n%%4==0,"nest","no nest")
  check_temporal_contract()
  ids<-check_schema(dat)
  parsed<-parse_focal_calendar_years(dat)
  require_true(identical(as.integer(parsed),as.integer(years)))
  for(cutoff in frozen_cutoffs) {
    sp<-forward_purge_indices(ids$bird,parsed,cutoff)
    require_true(sp$sample_counts$purged_forward_train_test_bird_overlap==0L)
    if(length(sp$test)>0L && length(sp$full_forward)>0L)
      require_true(max(parsed[sp$full_forward])<min(parsed[sp$test]))
  }
  # fit only one known-truth small model for speed: never source outcome data
  sp<-forward_purge_indices(ids$bird,parsed,2020L)
  if(count_gate(sp,"bird_purged_forward",ids$bird)$passes &&
     label_gate(binary_targets(dat)$HR,sp$bird_purged_forward,sp$test)) {
    pred<-fit_one(dat,binary_targets(dat),sp$bird_purged_forward,
                  sp$test,"HR",20261221L)
    require_true(is.finite(pred$test_brier) && pred$test_brier>=0 &&
      pred$test_brier<=1)
  }
  cat("GLOBAL_FORWARD_BIRD_PURGE_KNOWN_TRUTH_PASSED\n")
}

main<-function(args) {
  check_temporal_contract()
  if(length(args)==1L && identical(args[[1]],"--self-test")) {
    synthetic_test()
    return(invisible(TRUE))
  }
  require_true(length(args)==2L,"USAGE_TEMPORAL_MODEL_RDS_OUTPUT_JSON")
  out<-args[[2]]
  ok<-FALSE
  tryCatch({
    require_true(requireNamespace("ranger",quietly=TRUE) &&
      requireNamespace("jsonlite",quietly=TRUE))
    require_true(file.exists(args[[1]]) &&
      file.info(args[[1]])$size==53709803)
    x<-readRDS(args[[1]])
    require_true(is.list(x) && is.data.frame(x[["summary"]]))
    dat<-x[["summary"]]
    rm(x)
    result<-run_source_experiment(dat)
    jsonlite::write_json(result,out,pretty=TRUE,auto_unbox=TRUE,
      na="null",digits=NA)
    if(result$status=="RETROSPECTIVE_SWISS_CALENDAR_FORWARD_BIRD_PURGED_SOURCE_REFIT")
      ok<-TRUE
  },error=function(e){
    jsonlite::write_json(list(
      schema_version=1L,
      status="HOLD_SOURCE_YEAR_BIRD_FORWARD_ADMISSION_OR_CLASS_SUPPORT",
      error_type="SOURCE_YEAR_OR_MODEL_CONTRACT_HOLD",
      no_source_bird_IDs_GPS_labels_or_per_row_predictions_emitted=TRUE,
      original_BOP_terminal="empirical_state_prediction_mixed",
      redkite_external_terminal="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
    ),out,pretty=TRUE,auto_unbox=TRUE)
  })
  if(!ok)quit(save="no",status=1L)
}
if(sys.nframe()==0L) main(commandArgs(trailingOnly=TRUE))
