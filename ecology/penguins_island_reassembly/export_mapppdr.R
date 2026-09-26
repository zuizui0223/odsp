#!/usr/bin/env Rscript

# Export the APBP / mapppdr tables required by the frozen long-term extension.
#
# Recommended pin:
#   remotes::install_github("CCheCastaldo/mapppdr@88c73a507e0921b2541c218c71eaf16721bc6502")
#
# This script only materializes source tables. It does not inspect or select
# focal outcomes beyond the predeclared site-name and Pygoscelis filters.

suppressPackageStartupMessages(library(mapppdr))

args <- commandArgs(trailingOnly = TRUE)
out_dir <- if (length(args) >= 1) args[[1]] else "build/mapppdr"
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

data(penguin_obs)
data(sites)
data(species)

focal_sites <- sites[
  grepl("Biscoe|Dream|Torgersen", sites$site_name, ignore.case = TRUE),
  ,
  drop = FALSE
]

focal_species <- species[
  tolower(species$common_name) %in% c("adelie", "adélie", "chinstrap", "gentoo") |
    (species$genus == "Pygoscelis" &
       species$species %in% c("adeliae", "antarcticus", "papua")),
  ,
  drop = FALSE
]

focal_obs <- penguin_obs[
  penguin_obs$site_id %in% focal_sites$site_id &
    penguin_obs$species_id %in% focal_species$species_id,
  ,
  drop = FALSE
]

write.csv(focal_sites, file.path(out_dir, "sites.csv"), row.names = FALSE, na = "")
write.csv(focal_species, file.path(out_dir, "species.csv"), row.names = FALSE, na = "")
write.csv(focal_obs, file.path(out_dir, "penguin_obs.csv"), row.names = FALSE, na = "")

cat(sprintf(
  "exported %d sites, %d species rows and %d observations to %s\n",
  nrow(focal_sites), nrow(focal_species), nrow(focal_obs), out_dir
))
