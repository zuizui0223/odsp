# Gomes v6 tower-resolved acoustic stratum transfer — post-outcome, pre-tower-score freeze (2026-11-22)

## Source-semantic correction

A previously stated limitation, "*Gomes Bats.csv has no physical site ID*," was **incorrect**. It has an original `COLOR` categorical column with `green` and `red`. The [original peer-reviewed paper, Gomes et al. 2020, PeerJ 8:e10591](https://doi.org/10.7717/peerj.10591), states two COPAS canopy towers **180 m apart** and includes posterior random effects explicitly labeled `Tower=green` and `Tower=red`. The original checksum-pinned author `Hourly_Models.R` (MD5 `376bfc130acad070aa7045f6c816cd09`) uses `(1|COLOR)` as the tower/site random intercept. Therefore `COLOR` is an admissible **two-level physical tower identifier**. `X` remains a unique table row index, not a site key.

This correction supersedes the sentence in `docs/vertical_species_detected_count_transfer_real_v4_closeout.md` suggesting that independent tower holdout is impossible. The frozen previous v4 day-heldout scores and source receipts remain unchanged. The two towers are in the **same immediate forest, 180 m apart**: cross-tower evaluation is **local physical-tower transfer only**, not external geography, cross-community, cross-season or global SDM validation.

## Status before source COLOR-specific outcome opening

Original full Gomes source `Number` totals and v4 day-heldout scores have already been inspected. Thus v6 is an **explicitly post-original-outcome follow-up**, not an untouched preregistered confirmatory experiment. Nevertheless the following tower split, model and scoring rules are **frozen before examining tower-level scores**. No post-score tuning, choosing favorable tower direction, species subset or penalty search.

Original source immutability: Zenodo `10.5281/zenodo.4019867` v1 `Bats.csv`, size 901156, MD5 `2bc125dd0021d23c0efa0cb80828c632`, SHA256 `4a3b84e7175c29110bb6220f5cdf5889152897501b371fad3e2d9a74523773c9`, 7854 rows and 19 columns, 21 original Bat audio labels, 9 DAY, 13 HOUR, POS above/below; keep source `Number` as the nonnegative integer pass count; original source zeros remain zero. Only parse DAY,HOUR,Bat,POS,Number,COLOR; do not inspect original GPS, moonlight, or inferred flight heights. Verify exactly two tower labels `green` and `red` and original `Number` grand total 16123.

## Frozen prediction, outcomes and evaluation units

**Primary LOTO (two physical towers):**
- For each tower held out in turn, train **all nine nights** on the OTHER tower only. Score every original counted bat pass in heldout tower, using exact same heldout count cells for B0 and B1. Equal weight the two tower-level mean log scores for reported overall gain. Each tower score is count-weighted within tower (not each CSV row).
- B0 = `P(recorded POS | HOUR)`, trained solely from OTHER tower counts with symmetric Jeffreys pseudo-count alpha=0.5 per stratum. B1 = `P(recorded POS | HOUR, Bat acoustic label)` on same training; if Bat label has **<=5 training counts** (original author's exclusion threshold) or no counts in training at that HOUR, fall back exactly to B0. For an HOUR with no source-positive training across labels, fall both back to global train-only `P(POS)`. The SAME target tower and events are scored on both models, no target response enters training, class roster or smoothing.
- Report absolute B0 and B1, delta and number of counted calls **separately by tower**, plus equal-tower mean and sign-pattern. Two towers DO NOT support a population p value; no hypothesis is "accepted" based on two favorable signs.

**Secondary LOTO + NIGHT exclusion (18 tower×DAY cells):**
- For target tower `g` and source DAY `d`, train only on records with `COLOR !=g` AND `DAY !=d`. Test on records with `COLOR=g` AND `DAY=d`. Label eligibility and fallback are entirely train-only. Each target tower×DAY cell with >0 counted passes is scored; if any has 0, STOP this secondary rather than dropping favorable days. Report 18 deltas, mean across nine days within each tower then equal tower means. Do not count 18 folds as independent regions.
- No bootstrapped geographic confidence interval, no external source replication, and no new anthropogenic/weather/canopy predictors. Both variants are fixed, not model variants selected based on source results.

## What can and cannot be concluded

- Positive local cross-tower gain: audible species/complex label has useful information for predicting **recorded acoustic detector stratum at a different tower only 180 m away** after hour control, i.e. limited microspatial transfer. This is **not** automatically a 3D species occupancy SDM, a bat's true GPS/AGL height, latent niche partition, independent population universality, or a causal mechanism. No detector-specific `q_{species,tower,stratum,time}` calibration is available; microphone sensitivity and same-forest nightly conditions may dominate.
- Negative gain: this learned B1 rule does not transfer between the two local towers better than hourly base. Neither model's success/failure changes the previously frozen 9-DAY mixed endpoint.
- Two directions are all available physical towers; do not post-hoc select direction or label subset. If a source/semantic mismatch emerges, report STOP rather than inventing a third location.

This correction follows original author materials and is not inferred from number values or model response direction.
