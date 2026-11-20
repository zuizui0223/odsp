#!/usr/bin/env Rscript
# Strict outcome-blind GLOBAL calendar forward & biological-bird purge gate.
# Reuses the already frozen source-year parser in PR #297. Does not index
# HR/nest/success values or output animal-year IDs or individual locations.
args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=2L)stop("USAGE_TEMPORAL_PREFLIGHT_RDS_OUTPUT_JSON")
source("scripts/bop_swiss_ranger_focal_prior_year_v1.R",local=FALSE)
out<-args[[2]]
succeeded<-FALSE
tryCatch({
  require_true(requireNamespace("jsonlite",quietly=TRUE))
  contract<-jsonlite::read_json(
    "research/BOP_SWISS_TEMPORAL_BIRD_PURGE_V1_CONTRACT.json",
    simplifyVector=TRUE)
  require_true(identical(contract$contract_id,
    "bop-swiss-temporal-forward-bird-purged-ranger-v1"))
  require_true(identical(as.integer(contract$design$cutoffs),
    c(2020L,2021L,2022L)))
  require_true(contract$design$primary_cutoff==2021L)
  require_true(file.exists(args[[1]]) &&
    file.info(args[[1]])$size==53709803)
  obj<-readRDS(args[[1]])
  require_true(is.list(obj) && is.data.frame(obj[["summary"]]))
  dat<-obj[["summary"]]
  ids<-check_schema(dat)
  years<-parse_focal_calendar_years(dat)
  bird<-ids$bird
  require_true(min(years)==2016L && max(years)==2022L)
  rows<-lapply(c(2020L,2021L,2022L),function(cutoff) {
    test<-which(years>=cutoff)
    alltrain<-which(years<cutoff)
    testbird<-unique(bird[test])
    purge<-alltrain[!(bird[alltrain] %in% testbird)]
    require_true(length(intersect(unique(bird[purge]),testbird))==0L)
    require_true(length(intersect(alltrain,test))==0L &&
      length(intersect(purge,test))==0L)
    if(length(alltrain)>0L && length(test)>0L)
      require_true(max(years[alltrain])<min(years[test]))
    list(
      cutoff=cutoff,
      full_forward_train_seasons=length(alltrain),
      bird_purged_train_seasons=length(purge),
      forward_test_seasons=length(test),
      full_forward_train_birds=length(unique(bird[alltrain])),
      bird_purged_train_birds=length(unique(bird[purge])),
      forward_test_birds=length(testbird),
      full_forward_train_test_bird_overlap=length(intersect(unique(bird[alltrain]),testbird)),
      purged_train_test_bird_overlap=0L,
      forward_test_has_identical_year_IDs_across_models=TRUE,
      global_train_year_strictly_before_test_year=TRUE,
      sample_count_eligible=
        (length(purge)>=60L && length(test)>=20L &&
         length(unique(bird[purge]))>=20L && length(testbird)>=10L)
    )
  })
  require_true(length(rows)==3L && all(vapply(rows,function(x)
    x$purged_train_test_bird_overlap==0L,logical(1))))
  jsonlite::write_json(list(
    schema_version=1L,
    status="ORIGINAL_PREPARED_SOURCE_GLOBAL_YEAR_BIRD_PURGE_SCHEMA_CHECKED",
    source_697_258_id_histogram_verified=TRUE,
    source_calendar_year_range=c(min(years),max(years)),
    predeclared_cutoffs=c(2020L,2021L,2022L),
    primary_cutoff=2021L,
    source_only_count_arm_summaries=rows,
    outcome_values_accessed=FALSE,
    model_fit_run=FALSE,
    no_raw_animal_year_IDs_or_rows_in_output=TRUE,
    original_BOP_terminal="empirical_state_prediction_mixed",
    redkite_external_terminal="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
  ),out,pretty=TRUE,auto_unbox=TRUE,na="null")
  succeeded<-TRUE
},error=function(e) {
  jsonlite::write_json(list(
    schema_version=1L,
    status="HOLD_SOURCE_YEAR_BIRD_FORWARD_ADMISSION_OR_CLASS_SUPPORT",
    reason_type="ORIGINAL_RDS_OR_SOURCE_SCHEMA",
    outcome_values_accessed=FALSE,
    model_fit_run=FALSE,
    no_raw_animal_year_IDs_or_rows_in_output=TRUE,
    original_BOP_terminal="empirical_state_prediction_mixed",
    redkite_external_terminal="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
  ),out,pretty=TRUE,auto_unbox=TRUE)
})
if(!succeeded)quit(save="no",status=1L)
