# Swiss red-kite source GPS quality and biological-group multiplicity

**Freeze before access:** `research/BOP_RED_KITE_SUI_GPS_YEAR_ID_ADMISSION_V1_CONTRACT.json` committed at `4826226d4f3ac6d1f3af74191b0e6ebf53fb027f` on 19 Nov 2026, before this route's first Swiss source-GPS read.

## Scientific purpose

Oppel et al. (Journal of Avian Biology, DOI 10.1111/jav.03246) report **697 Swiss bird-seasons from 258 birds**, with 488/209 year-ID training/test rows and up to seven seasons per bird. The checksum-verified deposited `SUI_indseasondata.csv` instead contains **2,866 unique year IDs / 553 bird-ID strings before GPS filtering**. A paper count is not an authenticated training roster.

PR #293 confirmed the exact original 2024 ZIP's three NestTool training functions split on `year_id`, not `bird_id`. Its expected 67.463–146.540 birds represented in both roles is a **sharp range of expectations over unknown histograms**, not an actual split or measured accuracy bias. This gate attempts to recover the source's qualified bird-season multiplicities **without opening reproductive responses**.

## Frozen twelve-arm screening, not posthoc fitting

The paper specifies Swiss latitude strictly >45°N, longitude strictly >4°E, 11 March to 24 June and hour-scale sampling. The dated 2024 R source uses UTC ordinal DOY and `number_of_fixes > minlocs`; the upstream hourly downsampling implementation remains unknown. **Before data access**, we froze a 2 × 3 × 2 grid:

- Two seasons: fixed-2023 UTC DOY 70–175; or actual calendar March 11–June 24 (different in leap years).
- Three sampling schemes: all source events, one per UTC hour bin, or sorted rolling ≥3,600-second selection.
- Two GPS thresholds: >800 from dated R implementation, and ≥800 from paper wording.

Every arm is reported regardless of whether its two counts equal **697 seasons/258 birds**. The predeclared primary descriptive arm is fixed-DOY × unique UTC hour bin × >800, **not** a claim to reproduce the authors' original thinning. Count matching is not an identity or model-admission certificate.

## Exactly what is accessed

| Frozen source | Provider bytes | Provider MD5 | Parsed fields |
|---|---:|---|---|
| `SUI_indseasondata.csv` | 117,327 | `91394907a2d036e3dbacf5cd4f70475b` | Leading `bird_id,year,year_id` ONLY |
| `SUI_trackingdata.csv` | 266,416,454 | `f654300e9a77b8dc41221f44d468ea2c` | `bird_id,year_id,timestamp,long_wgs,lat_wgs` ONLY |

The mixed-response metadata CSV inevitably contains HR/nest/success bytes in transport for full-file MD5, but the prefix-only parser **never decodes the outcome suffix**. The GPS scanner uses coordinates and times transiently for filtering; it never exports any individual or hashed IDs, GPS positions, exact dates/timestamps, or track histories. No Movebank login, model RData or animal outcome values are accessed. Provider MD5, exact original header SHA256 and one-to-one year→bird identity are required. Failures are source HOLD.

## Methodological response (no biology prediction)

For each frozen arm, publish total eligible season IDs, distinct bird-ID strings, season multiplicity histogram (number of birds with 1,2,... eligible seasons), and the **expected** number of birds appearing in both roles under an explicitly hypothetical uniform year-ID train/test split of approximately 70/30. If a cohort has N season rows, n training rows and h_k birds with k seasons, its expected shared-bird count is sum(h_k*[1-falling(n,k)/falling(N,k)-falling(N-n,k)/falling(N,k)]).

This is conditioned on the *source* histogram; it is **not** the realized 2024 random split. An exact numerical match to 697/258 does not verify historical row identities, canonical animals, or forecast accuracy; the nest-success model uses a different smaller response-conditioned subset.

**Scientific terminals unchanged:** original ODSP BOP `empirical_state_prediction_mixed`; red-kite new-outcome and external-gain `HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER`; historical BOP Dryad `NOT_ADMITTED`.

## Reproducible run

```bash
python -m pytest tests/test_bop_red_kite_sui_gps_year_id_admission_v1.py
python scripts/bop_red_kite_sui_gps_year_id_admission_v1.py --out /tmp/sui-source-only.json
```

First official GitHub Actions source run is gated on Python 3.10/3.12/3.13 synthetic safety tests, with an aggregate-only first-result artifact even on source HOLD.
