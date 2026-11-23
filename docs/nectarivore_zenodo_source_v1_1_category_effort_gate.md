# Zenodo nectarivore v1.1 category-and-effort structure gate (before numeric outcome opening)

Source-only v1 original file MD5 and sheet/header audit **PASSED**: [GitHub Actions #45095211194](https://github.com/zuizui0223/odsp/actions/runs/45095211194), artifact 14781919595. Original author Zenodo DOI `10.5281/zenodo.10527420` version v2. Three original files and SHA256 frozen as verified:
- `CameraTraps.xlsx` MD5 `473bb5273b8f2e5369b4bfca0385b829`, SHA256 `b96a6c13e6826c284a32457cd680382cd855ad5bf34959e5695b7a2cfae84d1a`, 21,411 bytes, sheet `Data` A1:G181. Columns `ML_ID,Taxa,Inflorescences,Stratum,Abundance,Hours,Capture_rate`.
- `Mist-netting_bats.xlsx` MD5 `777acca28e0f59fc0103aac35daef92a`, SHA256 `9c5e402cc7cc6cd95b0e4ab1f5a306b0cc821905cd0ec27c619ca4b6af90b780`, 16,718 bytes, sheet `Mist-netting` A1:J128. Columns `Date,ML_ID,Type,Time,Species,Sex,Age,Net,Height,Feeding_guild`.
- `Nectar measurements_Strata.xlsx` MD5 `85e2a40e1a61421e19f86219fff87f9a`, SHA256 `29eb9197c9c28b8083c2a646ed5e3389bffa764566a6fdc8c673e6c0f43647cc`, 14,683 bytes, sheet `Nectar measurements` A1:M41. Columns `Year,ML_ID,Height,Stratum,Numb_of_nectaries,Time,Days_of_anth,Total_Nr_flowers,No_op_flow,Perc_op_flow,Nect_quant_mean,pH_value_mean,sugar_con_mean`.

**This v1.1 is separate from v1 and is committed BEFORE accessing any original numerical animal visits, captures, nectar quantity, concentration or pH.**

## Fixed permitted source fields and outputs

- Visit Data: parse **ML_ID, Taxa, Stratum**, and numerical deployment/exposure covariates **Hours** and **Inflorescences** (structural >0/missing counts only; do NOT expose individual numeric values). Do not read **Abundance** or **Capture_rate**.
- Bat mist-net data: parse **ML_ID, Type, Species, Net, Height, Feeding_guild** as observational design source labels/height classes only. Do not report bat species-specific vertical capture differences, individual counts per height/species, or any biological activity association. If numeric Height present, report range only as physically sampled height geometry, not as animal GPS flight height.
- Nectar Measurements: parse **ML_ID, Stratum, Year, Height** as metadata for paired spatial/temporal sampling only. Do not read columns `Numb_of_nectaries, Time, Days_of_anth, Total_Nr_flowers, No_op_flow, Perc_op_flow, Nect_quant_mean, pH_value_mean, sugar_con_mean` on this stage.
- Read the *Explanation* sheet for **textual documentation** of original units, no numerical biological data.
- Report only aggregate number of unique original IDs and source categorical code sets, number of plant×stratum support units by file, number of IDs shared by both Visit and Nectar sources, count of IDs with >=2 and >=3 **paired source strata**, and missing/malformed effort exposures in Visit table. Never output fine per-plant visit counts, heights, measured nectar values, or animal group × strata frequencies.
- Join keys must be exact `(ML_ID, Stratum)` with **no source label substitution**, unless Explanation explicitly defines an unambiguous equivalent name map and a separate v2 pre-outcome amendment is committed first. Do not assume lower-case string normalization resolves biology; exact labels only at this stage.
- If usable paired ID count <5 at >=2 strata, or Hours absent/invalid, or source-specific Taxa ID nonunique/undocumented, stop from a plant-heldout nectar/visitation model. No after-outcome merging across plant IDs or selectively dropping poorly sampled plants.

Successful source-only admission qualifies only **schema support**; before opening any original animal/nectar numeric fields, freeze v2 exact source row grain, visits/exposure unit, resource preprocessing, exclusions, plant heldout folds, two model arms, regularization, proper scoring, calibration-sensitivity and scientific claim ceiling. False 0 vs missing exposure must be considered.

All original PR #306/307/308 and frozen submitted papers untouched; no false claim of new site-independent 3D SDM.
