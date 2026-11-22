# Froidevaux et al. 2014: independent temperate-forest stratum table source and fixed descriptive target (2026-11-23)

**No new prospective biological confirmatory endpoint.** The primary published table was already inspected in the literature-search results before this contract; this is transparently a **published-source-open, exploratory comparison**, not a sealed prediction. No re-opening/tuning of the Gomes 2020 data or any frozen ODSP N2 endpoint.

## Study + public primary data

Froidevaux, Zellweger, Bollmann and Obrist (2014) `Optimizing passive acoustic sampling of bats in forests`, *Ecology and Evolution*, DOI [10.1002/ece3.1296](https://doi.org/10.1002/ece3.1296), public full text [PMC4278821](https://pmc.ncbi.nlm.nih.gov/articles/PMC4278821/), PubMed PMID 25558363. Original design: **8 landscape cells (1km²), 4 forest plots each (32 plots), 3 microphones per plot at gap, ground and canopy**, sampling 71 full nights and 145,433 sequences. Detectors randomly rotated to reduce particular-device biases. Forest ground 1.35m, canopy 13.5–30m (mean 18.9m). Published paper Table 1 provides 16 named taxa/acoustic groups and their total detected sequences by **gap, ground, canopy** (plus percentages) across the 32 plots; the table subset totals are **52,547 gap, 41,850 ground, 35,630 canopy** (130,027 table-assigned sequences). This is *not* the 145,433 total source sequence count. No raw species×plot×night outcome matrix has been obtained, and the paper's Table 1 aggregates across locations and times.

## Original-source extraction contract

Primary independent source endpoint: `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4278821/fullTextXML`. Download original journal fulltext XML, store SHA256 and XML length, identify the table by its explicit caption `Number of sequences per bat species recorded in each microhabitat`, and parse **count columns rather than percentages**. Fail closed if 16 taxon rows or the exact 3 table source totals disagree or if any row has negative, missing or noninteger counts; do not infer or impute missing plot/date labels. No hand-entered table from the earlier web search may substitute for original source bytes. If primary XML is inaccessible, record STOP; no unvalidated proxy. Archive only publication-level count table, source digest and derived metrics, which are public published data.

## Fixed measured target

**Main:** observed acoustic-label information about **recording position** in two *paired forest microhabitats*, ground vs canopy (exclude gap so not spuriously equated with vertical height). From the 16×2 published count table, calculate descriptive
`I(S;recorded layer)=sum_s,z p_s,z log[p_s,z/(p_s p_z)]` in nats; `H(layer)` in nats; `I/H(layer)` as fraction of observed layer entropy explained by acoustic label; and `exp(I)` for a unitless descriptive aid. No smoothing in information. Report total acoustic sequences (ground+canopy), number of nonzero classes, source-level 16 original labels, source original above/ground microhabitat counts, and unresolved species-complex labels. Calculate the 2-species hypothetic detector Gamma threshold `sqrt(max odds/min odds)` using **Jeffreys+0.5 per class/layer**, explicitly as detector-q *plug-in sensitivity* only, with no empirical q calibration.

**Original-author cited dominance sensitivity:** because the *published paper* reports exclusion of *Pipistrellus pipistrellus* from its guild activity modeling for severe dominance (this species accounts for ~87% sequences across all habitats), report the same information and standardized information on the exact remaining 15 published labels. This is a **descriptive contextual sensitivity**, not a new confirmatory or label-selected significance result. Do not silently prefer the result with a larger I.

## Cross-source comparability and bounds

Compare to authenticated Gomes et al. 2020 tropical two-tower, 9-day acoustic recorded-level endpoint (DOI 10.5281/zenodo.4019867), with **21 original labels**, original author `Number>5` leaves 17 labels. The existing v4 Gomes statistic is `I(Bat;recorded layer|HOUR)=0.17613037973692044` nats, whereas this Swiss Table 1 has no hour and can estimate only **unconditional I**; DO NOT directly claim an exact matched conditional cross-biome comparison or interpret larger/smaller I as more biological specialization. If a descriptive unconditional Gomes I is needed, declare a separately marked *post-outcome derived statistic* with the same fixed published counts and no new ecological hypothesizing; never retune source filters or use a new p-value. Different labels/hardware/studies and unknown q prevent same-species transfer and any latent height-use occupancy/3D SDM claim.

No independent-site or unobserved-night predictive validation can be computed from Swiss Table 1; 32 plots are documented in study methods, but not labeled in this table. Only published-level **qualitative pattern replication** in temperate vs tropical forest is allowed. Prior art in both papers already reports bat vertical/habitat stratification; do not overclaim novelty. Explicitly separate 'detector stratum' from bat flight height/AGL. Data are sequences/calls, **not independently observed bats**.

## Stop conditions

If no original fulltext XML or table values cannot be reconstructed unambiguously from publication bytes, return SOURCE_STOP and no synthetic numbers as measured result. New artifact should not alter ODSP main, frozen methods papers, JAE main, or PR #306 existing results.
