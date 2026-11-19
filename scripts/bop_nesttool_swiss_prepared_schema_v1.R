#!/usr/bin/env Rscript
# Original 2024 NestTool *prepared* RDS structural gate.
# Critical: do not inspect HR/nest/success VALUES in this stage.
args <- commandArgs(trailingOnly=TRUE)
if (length(args)!=2) stop("usage: Rscript source_schema.R pinned.rds output.json")
source_file <- args[[1]]
out <- args[[2]]
ensure <- function(x) if (!isTRUE(x)) stop("HOLD_PREPARED_RDS_SOURCE_SCHEMA_OR_ROSTER_MISMATCH")
status <- "HOLD_PREPARED_RDS_SOURCE_SCHEMA_OR_ROSTER_MISMATCH"
success <- FALSE

predictors <- c(
  "sex","revisits_day","residence_time_day","age_cy",
  "revisits_night","residence_time_night",
  "dist_max_day_to_max_night","median_day_dist_to_max_night","relative_dist_max_day_to_max_night",
  "revisitsSettle","revisitsIncu1","revisitsIncu2","revisitsChick1","revisitsChick2",
  "timeSettle","timeIncu1","timeIncu2","timeChick1","timeChick2",
  "meandayrevisitsBrood","lastvisitDay","maxtimeawayBrood2km","maxtimeawayBrood",
  "tottime_nest","Dist99Chick2","Dist99Settle","Dist99Incu1","Dist99Incu2","Dist99Chick1",
  "MCP95Chick2","MCP95Chick1","MCP95Incu1","MCP95Settle","MCP95Incu2"
)
hist_expect <- c("1"=66L,"2"=51L,"3"=62L,"4"=56L,"5"=20L,"6"=2L,"7"=1L)
require_source <- function() {
  ensure(file.exists(source_file) && file.info(source_file)$size==53709803)
  obj<-readRDS(source_file)
  ensure(is.list(obj) && "summary" %in% names(obj))
  dat<-obj[["summary"]]
  ensure(is.data.frame(dat))
  ensure(nrow(dat)==697L)
  ensure(all(c("bird_id","year_id","HR","nest",predictors) %in% names(dat)))
  # Only ID keys used; target values are never indexed or summarized.
  bird<-as.character(dat[["bird_id"]])
  year<-as.character(dat[["year_id"]])
  ensure(!anyNA(bird) && !anyNA(year) && all(nzchar(bird)) && all(nzchar(year)))
  ensure(anyDuplicated(year)==0L)
  ensure(length(unique(bird))==258L)
  multiplicities<-table(table(bird))
  actual<-setNames(as.integer(multiplicities),names(multiplicities))
  ensure(identical(actual,hist_expect))
  # Validate predictor columns EXIST without reading their values.
  list(status="PREPARED_SOURCE_SCHEMA_AND_697_258_HISTOGRAM_PASS",
       rds_byte_length=unname(file.info(source_file)$size),
       summary_seasons=nrow(dat),
       distinct_year_ID_strings=length(unique(year)),
       distinct_bird_ID_strings=length(unique(bird)),
       bird_season_histogram=hist_expect,
       feature_columns_present_count=length(predictors),
       targets_present=c("HR","nest"),
       outcome_label_values_inspected=FALSE,
       model_fit_run=FALSE,
       original_2024_training_roster_certified=FALSE,
       no_identifiers_emitted=TRUE,
       redkite_biological_terminal="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER")
}
encode_json <- function(obj) {
  if (!requireNamespace("jsonlite",quietly=TRUE))
    stop("MISSING_JSONLITE_SOURCE_GATE_DEPENDENCY")
  jsonlite::write_json(obj,out,auto_unbox=TRUE,pretty=TRUE,na="null")
}
tryCatch({
  result<-require_source()
  encode_json(result)
  success<-TRUE
},error=function(e) {
  encode_json(list(status=status,error_class="SOURCE_GATE_UNVERIFIED",
       no_identifiers_emitted=TRUE,outcome_label_values_inspected=FALSE,
       model_fit_run=FALSE,
       original_2024_training_roster_certified=FALSE,
       redkite_biological_terminal="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"))
})
if (!success) quit(save="no",status=1L)
