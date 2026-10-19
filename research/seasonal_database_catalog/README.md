# Seasonal ecology public-source inventory

This directory starts ODSP's own integration of public movement and camera databases for the [solar/ecological calendar hypothesis](../../docs/database_seasonal_ecology_programme_20261019.md).

## Frozen discovery frame: 2026-10-19

| Source | Scope | Records | Meaning |
| --- | --- | ---: | --- |
| [Movebank](2026-10-19/movebank/README.md) | Entire public Data packages collection | 437 | Archive packages; not 437 independent populations or seasonally eligible studies |
| [GBIF Camtrap DP](2026-10-19/camtrap/README.md) | Entire `endpointType=CAMTRAP_DP` dataset search | 26 | Registry datasets; native deployment and observation support still require screening |

The snapshots preserve provenance and discovery completeness. They do not constitute an animal-level movement database yet. Source metadata counts may overlap, issued dates are publication dates, and scientific-name strings are not a reconciled species taxonomy. Both positive and negative future biological results belong in the same cohort.

The research question is whether thermal and vegetation conditions explain within-individual changes in diel movement at matched photoperiod, across independent populations. The primary movement channel and complementary camera channel retain distinct measurements and observation models. See the programme document for predictions, data-table definitions, competing explanations, and the next event-level coverage analysis.

## Provenance and reuse

Preserve source DOI, authorship, version, original license statements, raw response hashes, and retrieval receipts. Conflicting license statements remain visible. The repository's code license does not replace a source data license. Catalog presence means discovery, not permission to redistribute every linked raw file.

Source endpoints:

- Movebank collection: <https://datarepository.movebank.org/handle/10255/3>
- Movebank discovery: <https://datarepository.movebank.org/server/api/discover/search/objects?scope=e1ae0743-5f80-4700-b21f-0535a10daee9&size=25&page=0>
- GBIF discovery: <https://api.gbif.org/v1/dataset/search?endpointType=CAMTRAP_DP&limit=100>

The individual source directories document exact reproduction commands and source-specific completeness checks.
