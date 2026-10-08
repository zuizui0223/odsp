# Rhode Island: does the winter/summer solar-clock reversal persist within a matched physical site and taxon?

Status: **FIRST OFFICIAL POST-OUTCOME MATCHED-SUPPORT DESCRIPTION COMPLETE**.
This is NOT an independent confirmation, a causal test, or a change to the
original frozen empirical decision. The scientific code and thresholds were
committed at a9df85a2 BEFORE the first matched result. First official
workflow 37766308999 replayed the original public RI v3 source and
astronomical prediction model without retuning.

## Why the existing aggregate was not sufficient

The original first exploratory RI v2 report found:

| Same heldout civil-clock target | Winter | Summer |
|---|---:|---:|
| All-detection, physical-site-equal seasonal mean, solar minus clock (nats) | +0.0274584593 | -0.0325742874 |

This FAILED the original both-seasons-positive hypothesis. Its scored
sample was 19,916 30-minute deduplicated detection events at 43 heldout
physical sites.

The first post-outcome taxon-standardization PR #226 found that averaging
12 provisionally selected mammal-named taxa *equally* gives winter
+0.00294 and summer -0.04097. But that summary had no joint
site×taxon×season×year data, and could not decide whether the apparent
season reversal occurred in the **same** taxa at the **same** places.
Taxon turnover, site turnover and the target weighting remained
unseparated.

## Matched support and exact source replay

The new study reads the SAME public RI v3 archive (MD5-pinned),
uses the original v2 parser, same physical primary site as the
entire-source train/heldout split, same 2018–21 training / 2022–23
heldout years, original species training-only admission, original
30-minute de-duplication, identical solar-phase-to-civil-clock
probability transport, smoothing and per-event log-score target.

Before any new descriptive result, the runner requires an exact
numerical replay of all of:

- 19,916 scored heldout events;
- 43 original heldout physical sites;
- winter +0.02745845931504319;
- summer -0.0325742873706785;

with winter/summer mean discrepancies at most 1e-10.

ALL conditions passed in the FIRST official workflow. This is an
important comparability safeguard: the new result is not based on
a different original prediction model or refitted favorable taxa.

For each (physical primary site, taxon), require at least 5 scored
detections in BOTH winter and summer (across the original two
heldout years). First calculate mean gain within each
site×taxon×season×year, then equally average represented years
within a season, and finally compare winter minus summer within
the same site×taxon cell.

This yields 135 matched cells at 42 physical sites across 12 reported
taxon labels. It does NOT assert that every matched cell contains
both 2022 and 2023. An independent taxon-wide year support indicator
is recorded, but does not prove both years in each particular cell.

## First real matched result: direction survives common support

| Descriptive target | Winter (nats) | Summer (nats) | Winter - summer (nats) |
|---|---:|---:|---:|
| 135 matched physical site×taxon cells, equally weighted | +0.02855 | -0.03874 | +0.06729 |
| 42 distinct physical sites weighted equally | +0.03372 | -0.04186 | +0.07558 |
| 12 taxa weighted equally after averaging their matched cells | +0.02821 | -0.03718 | +0.06539 |
| 96 matched cells with identified wild mammal-like binomials | +0.02375 | -0.06553 | +0.08928 |

Of 135 matched site×taxon cells, 93 have a larger solar-over-clock
gain in winter than summer, while 42 have the opposite.
There are 67 cells positive in winter and negative in summer,
and 15 cells negative in winter and positive in summer.

Thus the seasonal asymmetry is **not merely a comparison between
completely different species at completely different camera sites**.
The same taxon at the same primary camera site often shows higher
solar-versus-clock predictive improvement in winter than summer.
That is a new descriptive finding, not a formal proof that taxon
or location turnover contributes zero to the original pooled result.

## Why PR #226's taxon-equal winter mean was near zero but the new taxon-equal mean is positive

There is no numerical contradiction. PR #226 averages each taxon's
winter/summer mean over that season's AVAILABLE sites, for taxa that
pass site/event support, and lacks matched site×taxon cells.
The matched analysis retains only sites where each taxon has at
least five scored detections **in both seasons**. Its subset of
sites, matched taxa and weighting are DIFFERENT. It also includes
all original training-admitted labels, including unresolved
Bird and Rodentia groups, in the all-pairs primary descriptive
analysis. Consequently equal-taxonomic weighting in the two
analyses estimates two different observational populations.

It would be misleading to call this a randomized composition-effect
decomposition, an independently replicated result, or a correction
to the original empirical endpoint. The subset is conditional on
detectability in both seasons.

## Scientific interpretation and next discriminating measurement

The source has two compatible descriptive facts:

1. In the original site-heldout observational time score, a solar
   reference beats a fixed civil clock in winter but not summer.
2. That contrast persists descriptively within common physical
   site×taxon support. It does not vanish when completely different
   species or different sites are prevented from being the SOLE
   explanation.

The original wrong-season-sun negative control also scored worse
than the correctly dated sun in BOTH seasons, yet the solar model
still lost against fixed-clock prediction in summer. These two
comparisons are logically consistent: the sun can contain
information in summer without outperforming the clock model.

Potential explanations include: a stronger effective
sunrise/sunset constraint in winter, more season-specific foraging
or thermoregulation in summer, an inaccurate equinoctial phase
mapping, and changes in camera detection/maintenance/vegetation
or sampling effort. The archive cannot identify these causes
from detections alone. It is especially inappropriate to say an
individual animal changed its behaviour; taxon×site cells include
different unknown individuals and detection probabilities.

The next **genuinely new** empirical design should combine dated
independent operational camera effort logs, physically replicated
sites with camera uptime by clock hour, and an explicit comparison
of equinoctial/average sunrise–sunset anchors and fixed-clock
models on later untouched sites. A distinct dataset is required
for confirmatory inference. A temperature or prey interaction
cannot be inferred until those covariates or direct observations
are independently measured.

No p-values or new confidence intervals were produced in this
post-result matched-support route. None of ODSP's qualified
process-mean or historical terminal decisions changed.

## First-run provenance

- design commit: a9df85a29dbcf5bb0cf722c294591e8a09808e19;
- workflow: https://github.com/zuizui0223/odsp/actions/runs/37766308999;
- original score replay: PASS;
- first result artifact ID: 11544349015;
- artifact ZIP SHA-256: 1819b7d5c037204aaa613bf81f3089cda2d7bd0432e3fc04c37c24540c2c7691;
- first matched result JSON SHA-256:
  d661343de1fd17626e29b1f35a675c64bb82397d46f798a8c9e78fb7bccfd59e;
- post-result locked ledger:
  RI_SOLAR_V2_MATCHED_SITE_TAXON_FIRST_RESULT_LEDGER.json.

All of these concern an exploratory observation archive whose
timezone/clock calibration, site-sampling probabilities and
actual detection exposure remain unverified.
