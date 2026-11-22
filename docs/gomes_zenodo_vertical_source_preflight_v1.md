# Gomes et al. neotropical bat vertical/time data — source-only intake (2026-11-22)

This new prospective dataset is independent of the Dryad Yoh file whose official ZIP API returned HTTP401 in ODSP run #45029223793. No switch within a frozen *analysis* is made: the previous endpoint was **source admission only**, with no bat-pass numerical outcomes opened, and no ecological p-values estimated. The new dataset has a separately scoped admission task.

- Publication / data: Gomes et al. (2020), "Acoustic monitoring shows temporal variation in vertical stratification of neotropical rainforest bats", French Guiana; source release **Zenodo 10.5281/zenodo.4019867, v1, 2020-09-08**.
- Public exact file `Bats.csv`, published MD5 `2bc125dd0021d23c0efa0cb80828c632`, size ~901.2 kB; also original R analyses in record. Published design: 4 locations, 9 wet-season nights, above and below canopy monitoring. This work already showed vertical and hourly differences; those claims are author prior art.
- Single acquisition URL (version-pinned): `https://zenodo.org/records/4019867/files/Bats.csv?download=1`. Require this original MD5, record full SHA256 and file size, then read **header and line structure only**. No ecological outcome counts, bat species activity contrasts, modeled behavior or height effect is permitted in this source gate.
- Report only source URL, hashes, headers, row count and whether rows conform to header width. No sampled field values, species rankings, p-values or group support tests are authorized at this stage.
- After field inventory, draft a separate source-specific protocol choosing target event, height semantics, observational effort, group unit, strata, binning, species/sonotype identities, time variation and leave-out validation **before opening any original activity response**. Only record-event conditional `I(Species;detector strata|site,time,recorded)` could be estimated absent independent detection calibration. No calibrated ecological `I(S;true height|X)` is licensed.
- One-season/4-site/9-night sampling limits broad transfer/generalization even with positive detected-level heldout scores. Species/group detection range biases are **not** removed by simply sampling above and below canopy.
- If source URL returns 401/404 or hash mismatch, STOP with a source access/status receipt. Never invent counts or promote a synthetic demonstration to field evidence.

Existing frozen N2 ODSP and JAE publications are not modified.
