# GBIF Camtrap DP endpoint catalog — 2026-10-19

This directory preserves a **discovery catalog**, not an eligible analysis cohort. The GBIF registry query `endpointType=CAMTRAP_DP` returned 26 records at retrieval. All 26 are retained, including records whose titles or descriptions suggest acoustic, hair-trap, or other non-camera work. Neither a title-based exclusion nor an ecological outcome analysis was performed. Every row's same-station opposite-season support is `unknown` until its native package is screened.

## Files and provenance

| File | Contents | SHA-256 |
| --- | --- | --- |
| `gbif_camtrap_dp_search_full.json` | Unmodified JSON response to the registry search below | `b5b36a9e6c2f66616b328a538e1a09cfa07c6a408e0912fcccbb6b81794ef6f9` |
| `gbif_camtrap_dp_manifest.json` | Query URL and UTC retrieval time; all 26 dataset keys, titles, GBIF types, licenses, metadata temporal ranges, native endpoints, and per-dataset response hashes | `f5c26935bb81a1b436f22efde05ce377107750dc6f27963bbb240e47546a7f1a` |
| `gbif_camtrap_dp_catalog.csv` | Compact, normalized 26-row index, including GBIF DOI, publisher, license, metadata coverage, and canonical native Camtrap DP archive URL | `aa8b537e8e1639cb5064c55fb349d4ac643fd13af4bb27be4d2d2c85d3efe962` |
| `nphk1_deployment_screen.json` | Separate deployment-only feasibility check on one package | `82f0186ec5a6411d14a0f2dc25a3b096e6d9a9889276c7425dcafda96aa6c5b6` |

Registry request: `https://api.gbif.org/v1/dataset/search?endpointType=CAMTRAP_DP&limit=100`. The manifest records the exact UTC retrieval time (`2026-10-19T02:28:28.884976+00:00`) and the SHA-256 of the unmodified response. The registry reported `count=26`; the response contains 26 results with **26 distinct dataset keys**. This is complete for that endpoint-type query *at that retrieval time*, not a count of all camera-trap studies on GBIF or globally. A future run should follow pagination if `count` exceeds the requested limit. The CSV uses the search response for DOI/publisher/indexed record count and the canonical `GET /v1/dataset/{key}` response for native archive endpoints and metadata temporal ranges. Each per-dataset response URL, retrieval timestamp, and SHA-256 is in the manifest.

`metadataTemporalStart` and `metadataTemporalEnd` are the outer bounds of the publisher's **dataset-level metadata ranges**. `metadataTemporalRangesJSON` preserves all such ranges. These fields do not establish continuous camera operation, repeated stations, both opposite-solstice branches, local time correctness, or usable detection effort. `gbifIndexedRecordCount` is a registry value, not the number of independent animal events. The native archive's `deployments.csv` and `observations.csv` (or corresponding tables) must be evaluated for station-level eligibility and outcomes. GBIF notes that not all fields of a Camtrap DP package are necessarily harvested into its indexed representation: <https://docs.gbif.org/camera-trap-guide/en/#camtrap-dp>. The Camtrap DP format is specified at <https://camtrap-dp.tdwg.org/>.

## Reproduce discovery and retrieve canonical packages

```bash
curl -fsSL 'https://api.gbif.org/v1/dataset/search?endpointType=CAMTRAP_DP&limit=100' \
  -o gbif_camtrap_dp_search_current.json
jq -r '.count, (.results | length), ([.results[].key] | unique | length)' \
  gbif_camtrap_dp_search_current.json
sha256sum gbif_camtrap_dp_search_current.json

# Inspect the official detail record and its native Camtrap DP endpoint.
curl -fsSL 'https://api.gbif.org/v1/dataset/50cebe49-559b-42e8-955d-1df120b03f89' \
  | jq '{key,title,type,license,temporalCoverages,endpoints}'

# Download that record's native Camtrap DP package from its canonical endpoint.
curl -fL 'https://ipt.inbo.be/archive.do?r=nphk1' -o nphk1-camtrap-dp.zip
unzip -p nphk1-camtrap-dp.zip deployments.csv | head -n 2
```

For all current records, iterate the keys in the search response, request `https://api.gbif.org/v1/dataset/{key}`, and read the endpoint with `type=CAMTRAP_DP`; the exact 26 URLs are already in the CSV and manifest. The API documentation is <https://techdocs.gbif.org/en/openapi/v1/registry-principal-methods>. Live responses can differ from the frozen snapshot as publishers update datasets.

## Illustrative deployment-only feasibility check

The NPHK1 package is GBIF dataset `50cebe49-559b-42e8-955d-1df120b03f89`, native archive <https://ipt.inbo.be/archive.do?r=nphk1>. The downloaded archive had SHA-256 `c694bdcf117aedfa06bd02f77cbbb9d0615fa7a274f2e5d8ea1d6ece6e4895a9`; its `deployments.csv` had the table SHA-256 recorded in `nphk1_deployment_screen.json`. The table contained 1,414 deployments and 1,372 distinct `locationID` values. Summing inclusive deployment days by `locationID` across years found calendar-month effort in all twelve months, but **zero** location IDs with even one day in both March–April and September–October; the same was true at 14-, 30-, and 45-day thresholds. This illustrates why dataset-level year-round coverage cannot establish a same-station opposite-season comparison.

March–April versus September–October is only a fixed-window illustration for this Northern Hemisphere site, **not** a hemisphere-general eligibility rule or the final photoperiod-matching design. Overlapping deployments can double-count effort days in this quick screen. Repeated physical stations represented by inconsistent IDs would require reconciliation. No detection rates, species behavior, environmental relationships, or hypothesis outcomes were analyzed here.
