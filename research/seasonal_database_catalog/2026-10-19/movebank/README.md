# Movebank public data-package inventory — 2026-10-19

This directory is a **metadata inventory** of the Movebank Data Repository's public **Data packages** collection (handle `10255/3`, collection UUID `e1ae0743-5f80-4700-b21f-0535a10daee9`). It contains **437 distinct package UUIDs** across **18 scoped discovery pages**, not 437 independent biological studies or 437 qualified seasonal series. No event-level locations, tracks, seasonal measures, or biological outcomes were downloaded or computed.

The source was the anonymous public DSpace discovery API:

`https://datarepository.movebank.org/server/api/discover/search/objects?scope=e1ae0743-5f80-4700-b21f-0535a10daee9&size=25&page={page}`

Pages 0–17 were saved on **2026-10-19 UTC**. This receipt has **calendar-day precision**: individual HTTP request times were not recorded. The immutable raw responses are in `raw_pages.tar.gz`; `manifest.json` lists every uncompressed page hash, the concatenated raw-page SHA-256, and the archive SHA-256. The concatenated raw-page SHA-256 is `86d0be80408b4ebb2531c9554634d5457928f8406e537d05315b40aaee90785d`. The gzip tar SHA-256 is `3fcdb80407e15ce37486a63b007b17315d9fe0163b9cac127c6b81963f8d4135`.

`catalog.json` and `catalog.csv` preserve all DOI, license, license URI, scientific-name, sensor-name, and repository study-ID values per package as arrays. JSON arrays in CSV cells are encoded as JSON text. `publication_dates` are `dc.date.issued` values and `repository_accession_dates` are `dc.date.accessioned` values; **neither describes observation coverage**. `reported_animal_count` and `reported_location_count` are repository metadata and are **not deduplicated across packages, versions, or studies**. The title is descriptive source metadata; no title or outcome text was used to declare eligibility. Catalog inclusion means only that the package appeared in the public collection snapshot.

From the repository root, replay the committed raw archive offline:

```bash
python scripts/collect_movebank_seasonal_catalog.py \
  --replay research/seasonal_database_catalog/2026-10-19/movebank/raw_pages.tar.gz \
  --snapshot-date 2026-10-19 \
  --out /tmp/movebank-catalog-replay
```

To refresh from the public anonymous API on a new UTC date, choose a new output directory and provide that day's date. Requests are sequential, use 25 records per page, and have timeouts and retries:

```bash
python scripts/collect_movebank_seasonal_catalog.py \
  --fetch --snapshot-date YYYY-MM-DD \
  --out research/seasonal_database_catalog/YYYY-MM-DD/movebank
```

The initial snapshot was imported from already saved `page_000.json` through `page_017.json` files with `--import-pages DIR --snapshot-date 2026-10-19 --out research/seasonal_database_catalog/2026-10-19/movebank`. The collector rejects missing or duplicate pages, changing totals, duplicate package UUIDs, wrong collection scope, and non-package records before it writes a catalog. It does not assess whether a package has usable temporal, location, species, or licensing detail for a proposed hypothesis; that requires separate data-file and event-level qualification.
