#!/usr/bin/env Rscript
# Strict outcome-blind 2024 Swiss focal-bird calendar-year gate.
# This stage MUST succeed before the HR/nest response-model stage.
args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=2L)stop("USAGE_CHRONOLOGICAL_SCHEMA_SOURCE_RDS_OUTPUT_JSON")
source("scripts/bop_swiss_ranger_focal_prior_year_v1.R",local=FALSE)
outfile<-args[[2]]
succeeded<-FALSE
tryCatch({
  check_contract()
  input<-args[[1]]
  require_true(file.exists(input) && file.info(input)$size==53709803)
  obj<-readRDS(input)
  require_true(is.list(obj) && is.data.frame(obj[["summary"]]))
  dat<-obj[["summary"]]
  owner<-check_schema(dat)
  years<-parse_focal_calendar_years(dat)
  counts<-table(owner$bird)
  exactly_two<-names(counts)[as.integer(counts)==2L]
  require_true(length(exactly_two)==51L)
  chronological<-sum(vapply(exactly_two,function(b){
    a<-years[owner$bird==b]
    length(a)==2L && a[[1]]!=a[[2]]
  },logical(1)))
  require_true(chronological==51L)
  jsonlite::write_json(list(
    schema_version=1L,status="FOCAL_CHRONOLOGY_SCHEMA_51_TWO_SEASON_BIRDS_PASS",
    source_RDS_git_hash_verified_by_CI=TRUE,
    year_ID_strings=697L,bird_ID_strings=258L,
    two_season_birds_with_strict_temporal_order=chronological,
    verified_source_year_range=c(min(years),max(years)),
    test_birds_per_frozen_panel=50L,
    outcome_values_inspected=FALSE,
    model_fitted=FALSE,
    no_identifiers_GPS_or_individual_dates_exported=TRUE,
    redkite_external_terminal="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
  ),outfile,pretty=TRUE,auto_unbox=TRUE)
  succeeded<-TRUE
},error=function(e){
  jsonlite::write_json(list(schema_version=1L,status="HOLD_CHRONOLOGICAL_ID_YEAR_GATE",
    reason_class="SOURCE_YEAR_ID_SCHEMA_OR_ROSTER_UNVERIFIED",
    no_identifiers_GPS_or_individual_dates_exported=TRUE,
    outcome_values_inspected=FALSE,
    model_fitted=FALSE,
    redkite_external_terminal="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
  ),outfile,pretty=TRUE,auto_unbox=TRUE)
})
if(!succeeded)quit(save="no",status=1L)
