# Rhode Island solar-versus-clock: post-outcome taxonomic-composition diagnosis

**Exploratory and entirely post-outcome.** The source is the immutable
FIRST Rhode Island v2 result from GitHub Actions run 37747931559,
artifact 11535843980. This analysis does NOT reopen the Zenodo camera
images or rerun a scoring model. It verifies the receipt's exact SHA256
5d4bca0efc079ec3ae58d1062d4c1fb4c0b6476b64d56eead6d79e39ae83edab
before inspecting any per-taxon summary. The versioned analysis rules
were fixed in RI_SOLAR_V2_POSTOUTCOME_TAXON_COMPOSITION_CONTRACT.json
before this descriptive decomposition's first output was generated.

## Fixed first v2 ecological finding (never revised)

New-site, later-year solar-phase versus local-clock gains were:

| Group | Original mean log-score gain (nats/retained detection) |
|---|---:|
| Winter | +0.02745845931504319 |
| Summer | -0.0325742873706785 |

Original empirical decision: EXPLORATORY_NOT_SUPPORTED_OR_UNAVAILABLE.
The predeclared original hypothesis of solar advantage in BOTH
seasons was not supported. No post-result mammal-only subset,
favorable season, or alternative weight may rescue that status.

## What the first result can answer without further outcome access

The immutable result contains one record per *reported* taxon:
- total retained/scored detections across future years;
- physical heldout site count separately for winter and summer;
- site-averaged solar-over-clock mean log gain in each season.

It does NOT contain:
- species x site x year x season individual gains or events;
- a taxon-specific indicator of presence in BOTH 2022 and 2023;
- a season-specific event count for each taxon;
- a common within-taxon set of physically matching sites in winter and summer;
- raw detection exposure/effort in four-hour clock bins.

**Accordingly a winter/summer taxon mean contrast is not a
matched-site causal decomposition, and the contract's minimum two
future-year condition cannot be verified.**

## Transparently provisional taxon standardization

The post-outcome screening rule requires at least 8 physical sites
IN EACH season and 100 total scored detections. Exclude Aves sp.
(unresolved birds), Rodentia sp. (order-level), Meleagris gallopavo
(turkey) and Canis familiaris (domestic dog), as well as any other
taxon ending in sp. / without a two-token scientific name.

Under JUST the available site + total-detection filters,
12 binomial mammal-named taxa qualify PROVISIONALLY. Because the
two-future-year roster is absent, this is **not** 12 fully
predefined eligible taxa. The quantitative summary below is
only an illustrative taxon-standardized descriptive diagnostic:

| Descriptive comparison | Winter | Summer |
|---|---:|---:|
| Original pooled site-season mean | +0.02746 | -0.03257 |
| Equal average of 12 provisional taxon-site means | +0.00294 | -0.04097 |

Among these 12 provisional taxa, 6 had positive winter and
negative summer average gain, 2 had negative winter and positive
summer gain, and 4 were negative in both seasons. None was
positive in both seasons. Their equal-taxon winter-minus-summer
gain had mean +0.04391, median +0.06748, 25th percentile
-0.06758, and 75th percentile +0.13506.

This pattern supports an important caution: the apparent winter
benefit in the pooled result is not robust to a very different
taxonomic weighting. But it does **not** prove that a change in
taxon composition caused the pooled seasonal reversal. Species
and camera sites may change together. Equal taxon weights are
not the original site-weighted scientific estimand.

The four explicitly excluded nonwild/unresolved groups account
for 9,873 of the original 19,916 scored detections, about 49.57%.
These are combined counts across future years and seasons;
their *season-specific* shares cannot be recovered from the
first frozen per-taxon summary. Also, taxon summaries requiring
at least five sites are incomplete: their total can be less than
all scored events. Missing counts must never be assigned to
a taxon or season.

## Interpretation ceiling and next identifiable design

The present receipt can establish heterogeneity of sign between
taxa at the descriptive level. To distinguish:

A. taxonomic turnover alone;
B. within-taxon changes across seasons;
C. changing sites/detection effort within a taxon;

one would need an explicitly justified NEW post-exposure
analysis of matched site x taxon x season/year event summaries.
The correct decomposition holds the same set of sites and taxa
and changes one weighting factor at a time, with site-based
uncertainty and an explicit check of detection effort. Such a
route cannot be called an independent preregistered confirmation
on the same original archive.

Until then, the ecological conclusion is narrow:
solar-following is not uniformly predictive across seasons in
the original mixed detected-taxon survey. The taxon-standardized
diagnostic suggests pooled conclusions depend on ecological
composition, but the physical mechanism and contribution of
taxon turnover versus within-taxon plasticity remain unknown.

This document makes no causal claim, no new p-value/interval,
no population representativeness claim, and no change to
ODSP v5/source v0/fixed-set/future-refit routes or prior
empirical terminal records.
