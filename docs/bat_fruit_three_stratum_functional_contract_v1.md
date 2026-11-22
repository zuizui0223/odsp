# Three-stratum bat–fruit network: source-audited functional axis (2026-11-23)

**Status:** separate, **source-open exploratory** ecological source. This is NOT an independently preregistered test, a detected-acoustic replication, a calibrated latent 3D SDM or a proof of source-eating height. The raw public GitHub source matrices have already been inspected for checksum, structure and pooled reconciliation, before this contract was written. Do not label the subsequent test confirmatory or previously blinded.

## Original science and immutable source

Study: *Stratified sampling enhances the understanding of bat–fruit networks in the southern Atlantic Forest* (Oikos, DOI `10.1002/oik.11609`). Authors report 61 sampling nights from Sept 2013–Aug 2014 in the Salto Morato reserve, three forest mist-net capture strata: understory <=3m, subcanopy 4–8m, canopy >8m. Six nets per stratum/night (18 nets/night). This equal net **count** does NOT independently calibrate capture probabilities/effort by bat species, site, height or time.

Public original-author GitHub repository `karolportosupi/Bat-fruit-interaction`, freeze exact `main` commit `3d4ede895b9c5c2b9419f94458e3badb7440d932` before the new results, with four original source Git object blob SHA1:
- `Matriz_dossel.txt` (canopy): `47676a5696d5d00b869b95aa8a4c0055297410d7`.
- `Matriz_sub-dossel.txt` (subcanopy): `9a3fe231f611914a88bb09eb6ecb6d97d294aac2`.
- `Matriz_sub-bosque.txt` (understory): `a2c51fce68cac27f920f5cace74395521db1f6af`.
- `Matriz_tres_estratos.txt` (author-pooled 3-strata network): `bba476c853eca0602b6321055ec3ce53e2aed60b`.

Source filenames, canonical row/column identities and original-author R script `Script_reb.R` establish that counts are bat×plant interaction frequencies by capture strata. Confirm independently by parsing raw.githubusercontent.com at the pinned commit and computing `sha1("blob <byte length>\\0"+raw_bytes)` exactly; GitHub blob SHA is not the SHA256 of the file.

**Outcome-open source-integrity observations already seen:** Original three layer counts sum **canopy 61 + subcanopy 109 + understory 154 = 324**, matching the author-pooled matrix both total and **each bat×plant cell**; bat headings cover 9 names pooled (8 in understory, missing *Vampyressa_pussila* column), 37 plant names, and pooled 89 positive bat×plant cells. Strictly require these values; reconcile missing understory column as an omitted zero **only if the author-pooled matrix cellwise matches**. Reject duplicated bat names, duplicate plant labels, unexpected nonzero missing bat cells, negative/fractional counts, or any original Git blob mismatch. No manual taxonomic reassignment or plant identity merger beyond trimming whitespace.

## Primary *descriptive* resource-linked third-dimension question

For the observed `C(bat,plant,capture_stratum)` three-way interaction counts, not organism flight heights:

1. `I(Plant;Stratum|Bat)` nats. Does knowing the *capture stratum of the bat* reduce uncertainty about its **recorded** plant partner beyond bat label alone? This is exactly `H(Plant|Bat)−H(Plant|Bat,Stratum)`. Any positive *empirical* value is descriptive only (finite sparse contingency-table MI is biased upward).
2. `I(Bat;Stratum|Plant)` nats. Does stratum add recorded bat-label information given the plant label?
3. Ancillary, clearly distinct and purely descriptive: `I(Bat;Stratum)`, `I(Plant;Stratum)`, `I(Bat;Plant)`, source stratum counts, number of active bat×plant×stratum links, and the fraction `I(Plant;Stratum|Bat)/H(Plant|Bat)` for descriptive context. No habitat suitability mapping, overlap claims, plant dispersal distance or measured feeding-height mechanism.

## Locked source-open finite-count nulls

For the first CMI, preserve for every bat label its exact multiset of `Plant` and `Stratum` assignments (i.e., preserve bat×plant and bat×stratum margins); shuffle stratum labels **within each bat** over individual counted interaction tokens, 1999 Monte Carlo draws, fixed seed `20261123`. Compute a new CMI per permutation. Report observed CMI, null mean, excess, 95th/99th null quantiles and a conditional empirical upper-tail `(1+#null>=observed)/(1+1999)`. This tests statistical association under within-bat token exchangeability, NOT independence of biological bats/capture sessions, and is not a spatial/temporal generalization test.

For the complementary `I(Bat;Stratum|Plant)`, separately preserve per plant the bat×plant and plant×stratum margins; shuffle strata within plant, same 1999 draws and a distinct seed `20261124`. Report same null and excess, no corrected p-value that claims two independent studies. Neither null accounts for bat-specific capture probability, repeated animal recordings, source plant/fruit environmental differences across heights, sampling-availability or behavioral feedback. The exchangeability assumption itself is unverified.

**No new threshold search or species subset** is authorized after observing CMI. Presence/absence versions or equal-species macro MI are not automatic rescue endpoints. If original published matrix reconciliation fails, STOP before opening biological CMI; do not switch to a file subset or drop inconsistent taxa.

## Ecological interpretation ceiling

The records are observed *bat–plant interactions associated with the bat capture net stratum*. The actual **place where a bat ate fruit/seed was ingested is unknown**, so any phrasing that "plant feeding happens at these heights" is unsupported. Mist-net capture q varies with species morphology/flight height and stratum, and the captured bat-fruit events may repeat individuals across nights; net counts alone do not identify latent interaction availability. No independent site/night unit appears in the published aggregate matrices, so no out-of-sample transfer, SDM calibration or causal resource tracking can be claimed. Many plants are only `Sp1/Sp2` or `Piper_sp` labels; no ecological reidentification.

A positive beyond-null CMI would add a **functionally explicit observational example** of 3D information hidden by stratum pooling, complementing acoustic recorded-layer results in the independent `odsp` PR #306 without merging results, significance or claiming a universal trait strategy. A null/negative excess is equally legitimate and stays frozen. Prior author network-layer findings are prior art.

## Deliverable

New branch `prospective/bat-fruit-three-stratum-functional-20261123` based on ODSP `main`, independent of the frozen N2 manuscript and of PR #306. Save original Git provenance, full per-layer sum reconciliation, primary and complementary information measures, null receipts, known-truth tests and a result closeout, all without raw individual tracks or private sites. Do not modify ODSP main, existing batter JAE or esdm E5.
