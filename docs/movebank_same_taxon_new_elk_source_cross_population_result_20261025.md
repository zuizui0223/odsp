# Same taxon, different observed diel displacement: new source-verified elk comparison

**2026-10-25 | ODSP PR #267 | FIRST source-locked response from a previously uninspected independent published original elk data file.** This is an exploratory observational cohort comparison and NOT a confirmed species/population generalization, causal environmental explanation, or claim of nonoverlapping marked animals.

## Central biological question

The source-verified six-cohort Movebank study had recorded a clear positive NIGHT-relative GPS displacement change on the decreasing-photoperiod branch among its **12 admitted Canadian Ya Ha Tinda wapiti**, at near-matched summer-season daylength. Is the direction a general wapiti characteristic, or does another public GPS tracking cohort show a different observed seasonal change? This tests a specific within-species *source* prediction with newly accessed original observations, not another refinement of the original six-source temperature association.

## Before the new biological outcome

From the full pre-existing **437 public Movebank packages and 1,677 native ORIGINAL bitstreams**, exactly **three new single-taxon sources** were frozen in the [pre-outcome source-only roster](../research/MOVEBANK_SAME_TAXON_THREE_SOURCE_PREFLIGHT_20261025.json), by taxonomic species overlap with existing Alberta wolf, Virginia white-tailed deer, and Ya Ha Tinda elk source populations:

| Uninspected source | Taxon | DOI | Original published sensor file rows | Source-only result |
|---|---|---|---:|---|
| Yellowstone wolves | *Canis lupus* | [10.5441/001/1.717](https://doi.org/10.5441/001/1.717) | **23,604** | Original rows all failed the first timestamp/ID/location parsing gate; **SOURCE HOLD**, not a biological zero |
| Florida white-tailed deer | *Odocoileus virginianus* | [10.5441/001/1.293](https://doi.org/10.5441/001/1.293) | **40,811** | 15 marked source individuals but **zero year-cohorts with 10 matched rise/fall calendar date pairs**; source-effort insufficiency, not seasonal inactivity |
| Southwestern Alberta elk/wapiti | *Cervus elaphus* | [10.5441/001/1.j484vk24](https://doi.org/10.5441/001/1.j484vk24) | **878,116** | Original **235 individual×year samples** had ≥10 prospective same-astronomy source date pairs; only **20 marked animals** qualified after true 30–120min displacement interval rules |

Original provider metadata and file byte sizes were checked exactly; original MD5s were:
- Yellowstone wolves `c45f090bb797d6923e9360122f2ee156`, source original 3,854,637 bytes.
- Florida white-tailed deer `68f281b1fb6734febe2c13e9f0696ec6`, original 6,809,097 bytes.
- Southwestern Alberta elk `e25e57ba1c901305f26c9c2d03dcc67e`, original **149,867,434** bytes, with 171 original source individuals and 878,116 rows in the downloaded file.

All three provider ORIGINAL files passed MD5/byte checks; source taxon columns matched their archive's declared single taxon (no off-target rows). Before analyzing any new movement speed, source calendar opportunity and retained original individual ID/site observation coverage were audited *ephemerally* with the existing `inspect_csv` method, **without reading animal displacement**. Source-only CI [40159378985](https://github.com/zuizui0223/odsp/actions/runs/40159378985) passed all six known-truth tests, and its first original source-only aggregate JSON SHA256 `f4b884a36dd109b01db04a55ea9a81ccd413d74271febd6e90f1da15b11eda4f` was frozen. The two under-supported sources remain HOLD; they were not replaced by another file after seeing the result.

The **new GPS numerical endpoint** was frozen in [a separate contract](../research/MOVEBANK_THREE_NEW_SAME_TAXON_GPS_EFFECT_V0_20261025.json) BEFORE opening the new elk displacement values, with an unchanged, previously used and tested `scripts.movebank_solar_movement_20261019.analyze_file` algorithm. Original consecutive GPS steps 30–120 min, fully contained within a mean-solar DAY or NIGHT and one solar-local day, original step speed ≤60 km/h, ≥3 sampled steps per daypart per date, non-repeated rising/falling dates at modeled photoperiod ≤5-minute mismatch and ≥30d apart, a 0.5–2 source daypart sampling count balance, and ≥10 matched pairs per original animal/year: **none of these thresholds was retuned to admit more elk**. Original individual-year effects average equally within a marked animal and individuals equally within original source. The source-specific resampling range is conditional on the originally selected animals.

## New real observed cohort comparison

[**First original new-elk GPS effect CI 40159740853 SUCCESS**](https://github.com/zuizui0223/odsp/actions/runs/40159740853): all **five** tests, exact source-only artifact SHA, original elk checksum, original 878,116 file row count, original source solar-date support, single-taxon field and original estimator arithmetic were verified. The original first baseline Ya Ha Tinda relative displacement effect and its n=12 were checked against the prior frozen source receipt.

| Same original taxonomic species *Cervus elaphus* | Original GPS-qualified independently marked animals | ΔDAY log1p(km/h) | ΔNIGHT log1p(km/h) | Δ(NIGHT−DAY) log1p(km/h) | Source-animal conditional bootstrap 95% percentile range |
|---|---:|---:|---:|---:|---|
| **Ya Ha Tinda**/Canadian Rockies first source | **12** | **−0.024114** | **+0.020886** | **+0.045001** | **[+0.024092,+0.061865]** |
| **Southwestern Alberta** newly examined original source | **20** | **+0.006246** | **+0.003496** | **−0.002750** | **[−0.056914,+0.039323]** |

In the first Canadian cohort, the positive shift comprises **less sampled DAY displacement and more sampled NIGHT displacement**. In the newly tested same-species original cohort, sampled DAY and NIGHT GPS displacement both increase on the decreasing-daylight branch, DAY more than NIGHT, giving a source mean NIGHT-relative difference close to zero. Original animal signs are **13 positive, 7 negative** in the new source. Its conditional source-animal bootstrap spans positive and negative values, so there is **no clear demonstrated direction** in the new cohort.

This is *not* statistically established evidence that elk from two regions respond differently to the same temperature intervention, because the original Ya Ha Tinda cohort's n=12 may have differently sampled biological stage/years/sex/collars, and original source metadata have not yet established field-site recruitment independence or ruled out tracking-subject overlap. More importantly, the new cohorts' own date-specific ERA5 temperature, 30d P−ET0 and vegetation conditions were **not evaluated** in this source-response run; it is a SUN-MATCHED observational comparison, not a mechanism.

### Ecological contribution and what still needs proof

The **portable observation** is that a previously observed clear NIGHT-relative shift within one published elk source is **not reproduced as a comparably clear shift in a second original GPS source for the same named species**, even with the identical sun/step/date and sampling-effort algorithm. This cautions against assigning a species-global diel strategy from one well-sampled source. It improves on comparing a black bear to a deer across climates because taxonomy is held the same, while geography/protocol remain unconstrained. But with only two possible source populations and imperfect independence information, it does not infer heritable local adaptation or identify temperature, vegetation, reproduction or migration as the explanation.

The source-only difference (**235** preliminary individual×years versus **20** actual qualified distinct original individuals) also shows that raw camera/GPS timestamp opportunities can greatly overstate source information about strictly modeled 0.5–2h GPS displacement. Yellowstone and Florida are recorded as **source support limitations**, not negative replication experiments, and no threshold rescue was conducted.

## Reproducibility and non-disclosure

- First time-only original source/MD5/three-taxon audit: [CI 40159378985](https://github.com/zuizui0223/odsp/actions/runs/40159378985), artifact `movebank-yellowstone-wolves-florida-deer-alberta-elk-source-only-20261025`, ID **12585669605**. First source-only aggregate SHA `f4b884a36dd109b01db04a55ea9a81ccd413d74271febd6e90f1da15b11eda4f`.
- New original source effect: [CI 40159740853](https://github.com/zuizui0223/odsp/actions/runs/40159740853), aggregate artifact `original-elk-wolf-white-deer-same-taxonomy-biological-20261025`, ID **12586225754**. Five known-truth tests PASS and exact first-source source-only artifact replay.
- Frozen metadata-based [source roster](../research/MOVEBANK_SAME_TAXON_THREE_SOURCE_PREFLIGHT_20261025.json), [response contract](../research/MOVEBANK_THREE_NEW_SAME_TAXON_GPS_EFFECT_V0_20261025.json), source-only [code](../scripts/movebank_same_taxon_three_source_only_20261025.py), original first numerical [code](../scripts/movebank_three_same_taxon_original_gps_effect_20261025.py).
- Prior original six mammal GPS seasonal and ERA5 outcomes, earlier source-HOLDs, camera NDVI and alternative independent GPS duck speed results are **NOT rewritten or reclassified**.
- Original sensitive animal GPS coordinates, individual IDs, original movement interval rows and timestamps remain in ephemeral Actions runners, and were not committed or uploaded.

**Publication ceiling:** This is an exploratory first second-source *Cervus elaphus* comparison, not a robust species-wide replicated animal seasonal response and not field evidence for thermal or seasonal memory cause. PR #267 remains DRAFT.
