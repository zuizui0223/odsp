# Vertical bat/hummingbird–nectar resource, independent published source v1: pre-count admission

Date 2026-11-23 JST. New prospective source family on branch `prospective/nectarivore-vertical-resource-source-gate-20261123`, based on `odsp/main`; unrelated to frozen N2 and DRAFT #306–308.

## Authenticated upstream study and public source identity
Thiel, Heer et al. (2024), *Vertically Stratified Interactions Of Nectarivores And Nectar-Inhabiting Bacteria In A Liana Flowering Across Forest Strata*; original data record **Zenodo 10.5281/zenodo.10527420, v2 (2024-01-19)**. The source describes independent `Marcgravia longifolia` plant individuals, structured forest understory/midstory/canopy, animal visitation and local nectar chemistry. Files are **original author Excel XLSX workbooks**, not longitudinal species GPS/AGL tracks or an unbiased complete local community survey.

Declared source XLSX files (per original Zenodo v2 published MD5):
- `CameraTraps.xlsx` original MD5 **473bb5273b8f2e5369b4bfca0385b829**, size approximately 21.4KB: bat/bird/moth/marsupial **visit counts per liana and stratum**.
- `Mist-netting_bats.xlsx` MD5 **777acca28e0f59fc0103aac35daef92a**, size ~16.7KB: species-level bat captures by forest capture-height and liana/control location.
- `Nectar measurements_Strata.xlsx` MD5 **85e2a40e1a61421e19f86219fff87f9a**, size ~14.7KB: liana-level nectar volume/sugar/pH by stratum.

Version-fixed original downloader (one file at a time):
`https://zenodo.org/records/10527420/files/<URL-quoted original filename>?download=1`. Hash-authenticate all original bytes **before** any reading. Do not use mirrors, screenshots, or handwritten values in place of authentic originals.

## Source-only v1 gate BEFORE opening numeric nectar/animal counts

Read each XLSX with a real spreadsheet API (use `artifact_tool` for the initial local source assessment). Record file MD5/SHA256, workbook sheet names, sheet row/column dimensions, column header labels, which columns encode plant individual/source station, forest stratum, animal species/group, and visit/capture count or resource response, and README/explanation sheet headings. No numeric animal visits/captures, nectar volume, sugar concentration, pH or species × height contrast may be analyzed or printed in this first stage. If a file/source is inaccessible/hash mismatched, mark SOURCE_ACCESS_STOP.

An empirical, genuinely **plant-individual-heldout** resource-height comparison is possible only if: (i) common verifiable individual plant IDs and stratum semantics align between independent animal-visit and nectar workbooks; (ii) >=5 plant individuals have at least 2 paired recorded strata with both observations and nectar resource values; (iii) microphone/trap/net effort or camera effort is documented, distinguishing **zero visits** from **no camera deployment**; and (iv) at least 2 animal groups/sonotypes present with valid unambiguous source IDs. A bat species-level heldout prediction additionally requires same-event species by plant stratum exposure, not pooled mist-netting species counts from disparate controls.

If supported, **freeze a separate outcome v2 protocol before looking at numeric animal/nectar responses**: exactly specified animal group, exposure, plant heldout folds, per-stratum response, resource standardization, covariates, baseline/augmented model, penalty and proper scoring. Do not select a favorable stratum/taxon after seeing counts. If not supported, stop at descriptive original-source metadata and do not quietly reinterpret camera visits as echolocation or change the research question.

## Scientific ceiling
Study is a **single liana species** in one tropical forest study, not an external 3D bat SDM or universal cross-community mechanism. Forest strata were defined by vegetation structure and differ among individual lianas, and recorded bat height/net capture is not necessarily actual flower visitation/nectar ingestion height. Cameras and mist-nets have different, imperfect and species-dependent `q`. Even with plant-heldout positive scores, this would only establish **observed visit or sampling height predictability conditional on documented effort/nectar**, not latent organism height or a detection-corrected 3D SDM. Avoid claiming causal nectar-guided niche partition without independent treatments or instruments.

No changes to previous DRAFTs #306/#307/#308 or frozen ODSP N2, batter JAE, esdm E5.
