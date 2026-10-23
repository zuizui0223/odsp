# Seasonal ecology database: first implementation

## Goal

Make a central ecological hypothesis and its full public-source discovery frame concrete in the existing ecology branch. This revision produces the research specification and metadata inventories, not new animal-level ecological estimates.

## Tasks and verification

1. State the solar/ecological-calendar hypothesis, competing explanations, expected ecological patterns, independent sampling units, and limits of the existing discovery evidence in `docs/database_seasonal_ecology_programme_20261019.md`. The primary aim is comparative ecological inference; prediction is optional.
2. Enumerate every public Movebank Data package using the scoped DSpace collection. Keep exact source responses and checksums. Normalize provenance, multiple licenses, taxa, sensors, reported counts, and publication dates without assigning biological eligibility from titles or outcomes.
3. Preserve every GBIF Camtrap DP registry record and its native archive endpoint. Keep program date coverage separate from same-station seasonal coverage.
4. Implement minimal fetch/replay code and behavioral tests for missing/duplicate pages, accidental non-package entities, source count consistency, and preservation of ambiguous metadata. Replay the actual complete Movebank snapshot offline.
5. Check catalog counts and hashes, review scientific claims and changes, and append the verified work to existing draft PR #267. Do not merge or describe the metadata build as a completed ecological test.

Independent work: Movebank code/catalog and camera catalog have separate file ownership; root integrates the scientific specification and entry points. Next biological implementation starts with native-file and individual-deployment coverage, then fixes cohort, observation-support rule, ecological contrasts, and dependence groups before reading new movement effects. A training/holdout split is not required for the primary association analysis.
