#!/usr/bin/env Rscript
# Source: https://zenodo.org/records/21915776 (CC BY 4.0).
# This is run AFTER the independently frozen no-height 4-panel study/animal
# roster. Never select animals or source years using native GPS height values.
args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=3)stop("usage: source_pointwise.rds selected_gyps.tsv.gz schema.dput")
srcfile<-args[[1]];output<-args[[2]];schema_out<-args[[3]]
x<-readRDS(srcfile)
if(!is.data.frame(x))stop("Expected rectangular source flight data")
target<-c("122120597","352166254","44080734","972560688")
required<-c("study.id","study.name","species","individual.local.identifier",
    "tag.local.identifier","timestamp","location.long","location.lat",
    "track_flight_id","dataSource","height_gener","windSpeed_1000m",
    "Orographic_uplift_potential","w_star_Thermal_uplift_potential_(W*)",
    "flapping_prob")
missing<-setdiff(required,names(x))
if(length(missing)>0)stop(paste("Missing native columns",paste(missing,collapse=",")))
study<-as.character(x[["study.id"]])
sp<-as.character(x[["species"]])
sel<-which(
  (study=="122120597" & sp=="Gyps fulvus") |
  (study=="352166254" & sp=="Gyps africanus") |
  (study=="44080734" & sp=="Gyps fulvus") |
  (study=="972560688" & sp=="Gyps coprotheres")
)
# Study 352166254 also hosts Trigonoceps occipitalis; it is explicitly
# excluded by the taxon-specific outcome-blind source selection contract.
if(length(sel)<1000)stop("Selected source GPS study IDs appear unavailable")
optional<-intersect(c("height.above.ellipsoid","height.above.msl",
                      "dem","flapping_bin","meanVedba_Gs"),names(x))
required_all<-c(required,optional)
data<-as.data.frame(x)[sel,required_all,drop=FALSE]
names(data)[match(required,names(data))]<-c(
 "study_id","study_name","species","animal_id","tag_id",
 "timestamp","lon","lat","segment_id","data_source","height",
 "wind_speed_1000m","orographic_uplift","thermal_uplift",
 "flap_probability"
)
names(data)[names(data)=="meanVedba_Gs"]<-"vedba"
for (i in seq_along(data)) {
  if (inherits(data[[i]],"POSIXt")) {
    data[[i]]<-format(data[[i]],"%Y-%m-%d %H:%M:%S",tz="UTC")
  } else data[[i]]<-as.character(data[[i]])
}
dir.create(dirname(output),recursive=TRUE,showWarnings=FALSE)
write_con<-gzfile(output,open="wt")
write.table(data,file=write_con,sep="\t",row.names=FALSE,
            col.names=TRUE,quote=TRUE,qmethod="double",na="NA")
close(write_con)
schema<-list(
 source_archive="10.5281/zenodo.21915776",
 phase="AFTER_PROSPECTIVE_PREHEIGHT_SOURCE_GATE",
 n_native_rows=nrow(x),n_selected_rows=nrow(data),
 native_column_names=names(x),out_columns=names(data),
 study_ids=target,
 original_source_order_preserved=TRUE,
 result_depends_on_numeric_altitude_selection=FALSE,
 extraction_validation="All heights are exported *after* source IDs and eligibility criteria were frozen; never use native altitude presence to choose data source or target birds."
)
dput(schema,file=schema_out)
cat("Selected Gyps pointwise rows:",nrow(data),
    "\nNative altitude rows excluded from selection: 0",
    "\nSample source IDs:",paste(unique(data$study_id),collapse=","),"\n")
