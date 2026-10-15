# Official NIE EcoBank Uljin 1.1 landing recovered — 2026-10-14

## Distinct from previous SOURCE HOLD

The original DOI previously could not be resolved by the standard web retrieval route, but a JavaScript-aware HTTP extraction of the **DOI redirect** on 2026-10-14 resolved to the **official host**:

- DOI: https://doi.org/10.22756/ETC.20260000001022
- Exact official landing: https://www.nie-ecobank.kr/rdm/geodoi/selectRsrchDtaDtlVw.do?rsrchDtaId=RSD_0000000000012950
- Listed public downloadable attachment: `Uljin_camera_trap_ungulates_public_dataset_v1.1_20260305_EcoBank_revised.zip`
- Portal-displayed file size: **43,978 bytes**, which is *listing metadata*, not a byte-count verified against downloaded archive content.
- Portal-displayed dataset title retains `public dataset v1.0, 2026-03-05`, but **Version 1.1** appears in the attached ZIP filename and the official update history.
- Portal-displayed original release: **2026-03-09**, approval of update **2026-03-13 14:06:48** (Korean local time shown on portal).
- Portal version history describes revised coordinate generalisation in `site_covariates_public.csv` (public coordinates at lower precision), with corresponding `README_EcoBank.txt` and `MANIFEST.tsv` revisions. **Do not attempt to reconstruct protected camera coordinates.**
- The host describes its work as subject to KOGL; cite the original dataset under **KOGL Type 1 (attribution)** as documented by Jeon and Lim (2026), https://doi.org/10.3897/BDJ.14.e191556.

This is concrete **original-provider release discovery**, not a successful download or verified raw-data analysis. It supersedes only the **landing-page-discovery limitation** in the 2026-10-11 acquisition receipt; it does not supersede the scientific source admission contract or any prior result.

## Original file byte and integrity admission status

The official HTML shows a clickable **Download** affordance, but the HTTP text extraction did not expose a validated direct ZIP URL, local ZIP bytes, HTTP response headers for the ZIP, original independent published SHA256, or its internal member manifest. The browser click attempt was **not performed** (the connected paid web automation could not start because its wallet was out of credit). A separate standard URL retrieval route timed out/failed; that must not be interpreted as portal unavailability. Therefore:

`HOLD_ORIGINAL_V1P1_ZIP_BYTES_AND_INDEPENDENT_HASH_UNVERIFIED`

Do **not** infer from the filename or 43,978-byte listing that the archive contains source event rows or hour-exact operation intervals. Do **not** substitute journal supplementary plot archives or fabricated CSV data. Do **not** use a calculated local SHA256 alone as evidence of trusted official origin.

## Minimal reproducible follow-through (manual official download)

1. In a normal browser, visit the exact official NIE EcoBank URL above. Click the **Version 1.1 ZIP** attachment listed under `Data`, and retain the unmodified ZIP file. If login or permission is required, record that fact; do not bypass access controls.
2. Record the final download URL, retrieval date, release/version, host, any original release checksum or manifest, and the ZIP's actual local size and SHA256. Preserve site attribution; do not publish camera GPS.
3. Establish independent trust in downloaded bytes: official host download metadata/transport receipt plus a separately documented checksum or equivalent versioned release attestation. The **frozen v0** source feasibility contract requires independently attested SHA256. Where the host provides no external checksum, leave v0 on HOLD and document the external provenance alternative for scientific review; do not silently reinterpret a user-computed SHA256 as independent.
4. Verify expected original members **without leaking coordinates**:
   - `01_core_data/cameratrap_event_records.csv`
   - `01_core_data/camera_operation_log.csv`
   - `01_core_data/site_covariates_public.csv`
   - `03_documentation/MANIFEST.tsv`
5. Run the existing `scripts/run_uljin_original_v1p1_source_feasibility_v0.py` only with **qualified v0** original-source attestation and independently documented checksum, then independently normalise and verify station-by-date operation intervals before `scripts/run_uljin_ecological_zone_rates_v0.py`.

The original 41 daylength-matched calendar pairs (2022-05-01..06-10 rising and 2022-07-01..08-31 falling), all four focal ungulates, source-hour eligibility independent of detections, and H0/H1/H2/H3 scientific freeze remain untouched.

## Scientific interpretation remains bounded

No new empirical detections per 100 on-hours, source-event season-specific ecological contrasts, latent animal activity, temperature causation or evidence for competition has been obtained **from the original 82 days**. This receipt is an advance in identifying the authoritative data source, **not** a biological result.

Source links:

- https://doi.org/10.22756/ETC.20260000001022
- https://www.nie-ecobank.kr/rdm/geodoi/selectRsrchDtaDtlVw.do?rsrchDtaId=RSD_0000000000012950
- https://doi.org/10.3897/BDJ.14.e191556

## GitHub Actions public-host independent metadata verification — 2026-10-14

The separate source-only metadata probe `scripts/probe_uljin_ecobank_landing_v0.py` was tested by `tests/test_probe_uljin_ecobank_landing_v0.py` and run on a GitHub-hosted Python 3.11 runner. It made an HTTPS GET of the official DOI target and returned:

- HTTP **200**, exact **official** HTTPS host, official record identifier `RSD_0000000000012950`.
- The expected **Version 1.1 ZIP name** appears in actual provider HTML; the update history contains `1.1`.
- The download control is `href="javascript:..."`, with the public function name **`fn_atchFileDwldOpinionModal`**. No stable direct ZIP URL was exposed from the source HTML. This suggests a modal interaction rather than a plain static attachment URL, but **does not prove a login or payment requirement**.
- The probe records `original_zip_bytes_read=false`, `independent_sha256_attested=false`, `biological_effect_computed=false`, with status `OFFICIAL_LANDING_ZIP_LISTED_BYTES_NOT_DOWNLOADED`. It intentionally never logs JavaScript argument values, temporary tokens, event records, GPS or camera-hour fields.
- Focused 3/3 public-source metadata tests succeeded; original frozen biological source tests and assumptions were not changed.

Runs: https://github.com/zuizui0223/odsp/actions/runs/38421971398 and https://github.com/zuizui0223/odsp/actions/runs/38422415330.

**The source admission is still HOLD**. The definitive missing step is interacting with the official page's Version 1.1 attachment control and checking the unmodified archive with its release provenance; independent scientific inference remains unavailable until real operation hours are verified.


## Public download handler requires choosing user category and purpose — 2026-10-14

The companion read-only original-page JS audit `scripts/probe_uljin_ecobank_download_js_v0.py` inspected static first-party inline JavaScript (without submitting any HTTP form). GitHub Actions [run 38424632037](https://github.com/zuizui0223/odsp/actions/runs/38424632037) **PASSED** its privacy/error tests and obtained the following first-party control-flow facts:

- Clicking the official attachment calls `fn_atchFileDwldOpinionModal`, whose AJAX popup source path is `/rdm/selectAtchFileDwldPopup.do` and whose input variables include a dataset record and attachment identity.
- The next official function `fn_insertAtchFileDwldOpinion` checks a **user-category selection** and a **download/use-purpose selection**; a free-text “other” purpose appears to need at least two non-whitespace characters.
- It submits the selected inputs to `/rdm/insertAtchFileDwldOpinion.do`; **only if success is returned** does the page call `fn_egov_downFile` with the existing attachment identity. A separate error branch may redirect to `/uat/uia/egovLoginUsr.do`, but whether sign-in is compulsory for this release has **not** been established.
- This is an **interactive official user declaration**, NOT a static or broken ZIP URL. It must not be bypassed by directly invoking the lower-level download function or fabricating a user category or research-purpose declaration.

**Appropriate next official action:** From the [Version 1.1 source page](https://www.nie-ecobank.kr/rdm/geodoi/selectRsrchDtaDtlVw.do?rsrchDtaId=RSD_0000000000012950), click the ZIP entry, select the **actual** user category and the accurate scientific-research use purpose, and complete the official portal's permitted download workflow. The present automated source-only check intentionally **did not submit such a declaration**; no original ZIP bytes, member data, independent SHA256, real 82-day animal rates or original operation hours were obtained. If login is demanded, document the provider's requested account path; do not work around controls.

The biology paper Table 3 reanalysis is **separate** from this original-source hold, documented at `docs/uljin_published_four_taxon_seasonal_detection_difference_20261014.md`. It uses already-published coefficients with an unknown-covariance and six-comparison Bonferroni bound and cannot be relabelled as the original 41-day data analysis.
