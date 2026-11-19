#!/usr/bin/env Rscript
# Model-stage ONLY. Executed after successful outcome-blind source-schema gate.
# Exports a volatile runner-private table of the 34 predeclared source
# predictors, year-ID/bird-ID keys, and ONLY HR/nest targets; never 'success'.
args <- commandArgs(trailingOnly=TRUE)
if (length(args)!=2) stop("usage: Rscript export_refit.R pinned.rds temp_table.csv")
file<-args[[1]]
dest<-args[[2]]
ensure <- function(ok) if (!isTRUE(ok)) stop("HOLD_PREPARED_RDS_SOURCE_SCHEMA_OR_ROSTER_MISMATCH")
features <- c(
 "sex","revisits_day","residence_time_day","age_cy",
 "revisits_night","residence_time_night","dist_max_day_to_max_night",
 "median_day_dist_to_max_night","relative_dist_max_day_to_max_night",
 "revisitsSettle","revisitsIncu1","revisitsIncu2","revisitsChick1","revisitsChick2",
 "timeSettle","timeIncu1","timeIncu2","timeChick1","timeChick2",
 "meandayrevisitsBrood","lastvisitDay","maxtimeawayBrood2km","maxtimeawayBrood",
 "tottime_nest","Dist99Chick2","Dist99Settle","Dist99Incu1","Dist99Incu2","Dist99Chick1",
 "MCP95Chick2","MCP95Chick1","MCP95Incu1","MCP95Settle","MCP95Incu2"
)
ensure(file.exists(file) && file.info(file)$size==53709803)
obj<-readRDS(file)
ensure(is.list(obj) && "summary" %in% names(obj) && is.data.frame(obj$summary))
s<-obj$summary
ensure(nrow(s)==697L && all(c("year_id","bird_id","HR","nest",features) %in% names(s)))
year<-as.character(s[["year_id"]])
bird<-as.character(s[["bird_id"]])
ensure(!anyNA(year) && !anyNA(bird) && anyDuplicated(year)==0L && length(unique(bird))==258L)
actual<-table(table(bird))
ensure(identical(setNames(as.integer(actual),names(actual)),
 c("1"=66L,"2"=51L,"3"=62L,"4"=56L,"5"=20L,"6"=2L,"7"=1L)))
sel<-c("year_id","bird_id",features,"HR","nest")
out<-s[,sel,drop=FALSE]
out$year_id<-year
out$bird_id<-bird
for (k in features) out[[k]]<-as.character(out[[k]])
for (k in c("HR","nest")) out[[k]]<-as.character(out[[k]])
write.csv(out,dest,row.names=FALSE,na="",quote=TRUE)
# Never output actual source identifiers, labels, values, or line fragments.
cat("SOURCE_RDS_SCHEMA_PASS_PRIVATE_MODEL_INPUT_WRITTEN_NO_ROWS_PRINTED\n")
