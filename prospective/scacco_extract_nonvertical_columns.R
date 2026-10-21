#!/usr/bin/env Rscript
# Export ONLY nonvertical metadata of the newly licensed 2026 cross-guild archive.
# readRDS necessarily deserializes the complete R object, including GPS height
# columns, BUT NO numeric altitude value is inspected or used for admission.
# Never call summary/mean/quantile/is.na on height columns in this script.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3) stop("usage: source.rds meta.tsv.gz schema.json")

infile <- args[[1]]
outfile <- args[[2]]
schemafile <- args[[3]]
set.seed(20261021)
x <- readRDS(infile)
if (!is.data.frame(x)) stop("Source RDS is not a rectangular flight dataframe")

native <- names(x)
required <- c(
  "study.id","study.name","species","individual.local.identifier",
  "timestamp","location.long","location.lat","track_flight_id",
  "dataSource","flapping_prob","meanVedba_Gs",
  "windSpeed_1000m","Orographic_uplift_potential",
  "w_star_Thermal_uplift_potential_(W*)"
)
missing <- setdiff(required,native)
if (length(missing)>0) stop(paste("Required non-height fields unavailable:",
                                paste(missing,collapse=",")))

# Frozen plan permits native height fields to exist, but does not permit
# testing any of their values for admissibility or group assignment.
height_fields <- grep("height|altitude",native,value=TRUE,ignore.case=TRUE)
f <- x[required]
names(f) <- c("study_id","study_name","species","animal_id","timestamp",
              "lon","lat","segment_id","data_source","flap_probability",
              "vedba","wind_speed_1000m","orographic_uplift",
              "thermal_uplift")
for (i in seq_along(f)) {
  if (inherits(f[[i]], "POSIXt")) {
    f[[i]] <- format(f[[i]],"%Y-%m-%d %H:%M:%S", tz="UTC")
  } else {
    f[[i]] <- as.character(f[[i]])
  }
}
dir.create(dirname(outfile),recursive=TRUE,showWarnings=FALSE)
con <- gzfile(outfile,open="wt")
write.table(f,file=con,row.names=FALSE,col.names=TRUE,sep="\t",
            quote=TRUE,na="NA",qmethod="double")
close(con)
schema <- list(
  study="Scacco 2026 38-species birds-and-bats biologging points",
  source_doi="10.5281/zenodo.21915776",
  source_rows=nrow(x),
  native_columns=native,
  native_class_by_column=sapply(x,function(z) paste(class(z),collapse="/")),
  height_column_names_only=height_fields,
  nonvertical_export_names=names(f),
  export_rows=nrow(f),
  numerical_height_accessed=FALSE,
  numerical_height_completeness_tested=FALSE,
  biological_effect_computed=FALSE,
  caveat="Native source deserialized as full RDS; no vertical value was consulted for metadata export."
)
# No dependency on jsonlite; the schema is emitted as R's dput text and
# a Python wrapper inspects the frozen TSV header and exact row count.
dput(schema,file=schemafile)
cat("Nonvertical fields exported:",paste(names(f),collapse=","),
    "\nrows:",nrow(f),"\nheight outcomes inspected: FALSE\n")
