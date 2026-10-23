# Seasonal ecology public-source inventory

This directory starts ODSP's own integration of public movement and camera databases for the [solar/ecological calendar hypothesis](../../docs/database_seasonal_ecology_programme_20261019.md).

## Frozen discovery frame: 2026-10-19

| Source | Scope | Records | Meaning |
| --- | --- | ---: | --- |
| [Movebank](2026-10-19/movebank/README.md) | Entire public Data packages collection | 437 | Archive packages; not 437 independent populations or seasonally eligible studies |
| [GBIF Camtrap DP](2026-10-19/camtrap/README.md) | Entire `endpointType=CAMTRAP_DP` dataset search | 26 | Registry datasets; native deployment and observation support still require screening |

The original discovery snapshots preserve provenance and registry completeness, **not** a globally representative animal movement cohort. Separate first-party MD5-replayed Movebank GPS analyses have now admitted **six original recruitment cohorts, 197 marked individuals**, with individual solar-date matched GPS movement results and coarse modelled regional ERA5 environment at the same matched dates. This is a **separate qualified analysis subset** of the 437-item discovery frame, not a biological result from all 437 packages. Four additional attempted original files were source MD5 HOLD and one moose file lacked eligible individuals. Original source metadata counts may overlap; published dates are NOT observation times. All original source records and zero/hold outcomes must remain visible.

The research question is how thermal and vegetation conditions relate to within-individual changes in diel movement at matched photoperiod, and how those relationships vary among independently sampled populations and taxa. The primary aim is comparative ecological inference; predictive accuracy is optional. The primary movement channel and complementary camera channel retain distinct measurements and observation models. See the programme document for expected ecological patterns, data-table definitions, competing explanations, and the next event-level coverage analysis.

## Qualified real-data ecological results (2026-10-19)

- [Six source-verified mammal GPS cohorts and their matched-date ERA5 regional hydrothermal context](../../docs/movebank_six_original_cohort_matched_era5_complete_ecological_result_20261019.md): original 197 marked mammals, all six regions with positive modeled source daylength-decreasing air-temperature contrast and heterogeneous observed NIGHT−DAY GPS displacement; [source MD5, five tests and ERA5 CI](https://github.com/zuizui0223/odsp/actions/runs/39214116116).
- [Same individual's original matched-date climate–movement ecological association across all six cohorts](../../docs/movebank_six_source_within_animal_era5_thermal_water_ecology_20261019.md): source-checked temperature and P−ET0 observational slopes, including positive within-animal thermal co-trend in 31/33 Virginia deer despite near-zero source mean season effect; [six-test outcome CI](https://github.com/zuizui0223/odsp/actions/runs/39217223363).
- [Movebank-sourced comparative ecology manuscript v0.3](../../manuscript/MOVEBANK_EQUAL_DAYLIGHT_DIVERGENT_MAMMALS_ECOLOGY_v0.md): original source differences and their observational, source-specific caveats. **No causal animal heat response or global law supported.**
- Complementary camera-trap work is a DIFFERENT measurement process; see [separate Serengeti ecology manuscript](../../manuscript/SOLAR_SEASONAL_HYSTERESIS_ECOLOGY_PAPER_v0.md). The 26 Camtrap DP entries remain *discovered* rather than 26 qualified recurring camera stations.

## Provenance and reuse

Preserve source DOI, authorship, version, original license statements, raw response hashes, and retrieval receipts. Conflicting license statements remain visible. The repository's code license does not replace a source data license. Catalog presence means discovery, not permission to redistribute every linked raw file.

Source endpoints:

- Movebank collection: <https://datarepository.movebank.org/handle/10255/3>
- Movebank discovery: <https://datarepository.movebank.org/server/api/discover/search/objects?scope=e1ae0743-5f80-4700-b21f-0535a10daee9&size=25&page=0>
- GBIF discovery: <https://api.gbif.org/v1/dataset/search?endpointType=CAMTRAP_DP&limit=100>

The individual source directories document exact reproduction commands and source-specific completeness checks.
