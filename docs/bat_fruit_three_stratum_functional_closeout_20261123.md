# Original bat–fruit three-stratum information: source-authenticated result and independent audit (2026-11-23)

**Result tier:** public original author source, aggregated bat–fruit records, **source-open exploratory** fixed-margin randomization and independent arithmetic recheck. No source-based test was preregistered before the original published layer counts were seen; this is neither an independent masked holdout nor general high-dimensional SDM inference. This is a **separate unmerged ODSP branch** and does not alter the frozen N2 manuscript, `batter` JAE main or `esdm` E5.

## Original author and source identity

*Stratified sampling enhances the understanding of bat–fruit networks in the southern Atlantic Forest*, Oikos (DOI [10.1002/oik.11609](https://doi.org/10.1002/oik.11609)), field sampling reported for **61 nights** in Sep 2013–Aug 2014, equal numbers (six) of mist nets nominally placed in each of three forest strata: forest understory up to 3 m, subcanopy 4–8 m and canopy >8 m. These are bat **capture strata**, not observed fruit-eating locations. Different net heights/flight maneuvers/fruit sources can still create variable detection and encounter probabilities; equal net count does not calibrate q. The paper already asks about stratified bat–fruit networks; it is important prior art.

Original-author public GitHub `karolportosupi/Bat-fruit-interaction` pinned to commit **`3d4ede895b9c5c2b9419f94458e3badb7440d932`**. All 4 original source Git blob SHA1 identifiers, source SHA256 and sizes independently authenticated against raw.githubusercontent.com; see [protocol](bat_fruit_three_stratum_functional_contract_v1.md) and [v1 successful CI](https://github.com/zuizui0223/odsp/actions/runs/45081870409), artifact **14777576901** `bat-fruit-three-stratum-functional-v1`. The source formula also independently compares every bat×plant original author-pooled cell to the three stratum source matrices.

| Forest net capture stratum | Recorded bat–fruit interaction frequencies | Positive bat×plant cells |
|---|---:|---:|
| Canopy >8m | 61 | 31 |
| Subcanopy 4–8m | 109 | 46 |
| Understory ≤3m | 154 | 58 |
| **Sum** | **324** | **89 unique bat×plant pairs after pooling layers** |

The original bat × plant pooled matrix contains **nine bat species labels × 37 plant species/anonymous codes**, 89 positive pair cells. The source understory matrix lacks the ninth bat column; this source column absence was reconciled at exact zero per bat×plant cell against original published pooled totals, and not interpreted as independent proof of biological absence. No source taxon aliases were silently reconciled/renamed; source raw labels and anonymous plant codes remain original.

## Frozen *source-open* information questions

For count tensor `C(B,P,Z)` (Bat×Plant×**capture stratum**), original counts weighted:

`I(P;Z|B) = H(P|B)-H(P|B,Z)`.

`I(B;Z|P) = H(B|P)-H(B|P,Z)`.

For each, a corresponding **1999 fixed-margin token-shuffle** null was computed:
- primary: shuffle Z within each bat, retaining bat×plant and bat×stratum source counts;
- complement: shuffle Z within each plant, retaining bat×plant and plant×stratum counts.
These nulls test *interaction-count exchangeability* only; repeated bat individuals/nights, unequal capture probabilities and plant resource availability were not modeled. Monte Carlo p is one-sided conditional on those assumptions. Under a sparse multiway table, **a positive raw conditional MI by itself is not evidence of ecological specialization**.

| Source-open question | Observed CMI nats | Frozen-margin null mean nats | Excess over null | Upper-tail Monte Carlo p |
|---|---:|---:|---:|---:|
| Does a *given bat label* record a different plant partner in different capture strata? `I(P;Z|B)` | **0.2581875907** | 0.2428811658 | +0.0153064249 | **0.2000** |
| Does capture-stratum identity distinguish bat species *conditional on the given plant partner*? `I(B;Z|P)` | **0.2449384764** | 0.1722039187 | +0.0727345577 | **0.0005** |

The **first result is not above the fixed-margin null**: source evidence does **not** support saying individual bat species change plant partners with capture height in excess of sparse-count expectations. The complementary result *is* above its different fixed-margin null: **given an observed plant partner, captured bat-label composition retains height-layer organization** beyond that conditional permutation baseline. There are no independent bat individuals or spatial plots as inferential units, so p=0.0005 is **not a population-level ecological p-value**, not proof of net capture-q-invariant space use, causal feeding choice or across-night transfer.

Original descriptive complementary entropy: `H(B|P)=1.2306328518` and `H(B|P,Z)=0.9856943753`, yielding `0.2449384764` nats. Original descriptive primary entropy: `H(P|B)=2.1228944756`, `H(P|B,Z)=1.8647068848`, yielding `0.2581875907` nats; **12.16% apparent uncertainty reduction**, mostly explained by finite-count null. These **in-sample** entropy percentages are not cross-validated forecasting gains.

Other observed raw source descriptors: `I(B;Z)=0.2051162941`, `I(P;Z)=0.2183654084`, `I(B;P)=0.5876537702` nats. These conditionals and marginals are standard information-theory metrics, not newly invented biological mechanisms.

## Independent implementation and quantitative check

A separate fresh-source parser, NumPy 3D matrix build and *different* entropy-identity implementation (no production v1 helper imported) independently reverified the four original source Git blobs and every original pooled margin. Script: `scripts/verify_bat_fruit_stratum_v2_independent.py`.

[Successful independent CI #45082041253](https://github.com/zuizui0223/odsp/actions/runs/45082041253), artifact **14776549960** `bat-fruit-stratum-v2-independent`.

- **Exact original CMI reproduction:** absolute errors `1.05×10⁻¹⁵` (primary) and `5.55×10⁻¹⁶` (complement).
- Independently reshuffled original fixed margins with NumPy RNG and distinct seeds, 1,999 randomizations **again**. Primary null mean **0.2434700**, excess **+0.0147175**, tail **p=0.212** (not beyond null). Complement null mean **0.1720931**, excess **+0.0728454**, tail **p=0.0005** (above null). **Qualitative classifications reproduced** under an independent implementation and RNG.
- **Six** source-free mathematical/schema tests passed in the original v1 CI. The first Action attempt did not open the source because one synthetic-only fixture had one bat column, below the parser's minimum two; the test fixture was corrected, and the scientific protocol, original thresholds and biological matrices were not modified afterward.

## Biological meaning and ceiling

The measured extra dimension has a **functionally relevant label (plant partner)**, not only recorded detector height. This shows how one can ask whether recording height changes plant–bat **network composition** after controlling for plant label or bat label. It does **not establish how high fruits were consumed**, why a bat moved to a height, vertical behavioral specialization of the same individual, actual plant availability or plant resource use causation, nor a sensor-calibrated 3D latent SDM.

This is **not** independent geographical generalization; all stratum matrices are pooled across the original ~61-night study, with no individually identified capture-night, animal, recording-effort exposure or site-level holdout available in these files. Source counts reflect mist-net capture and plant-partner recovery processes, both potentially biased by species/height/diet, and may include repeated individuals. The source labels include unidentified plants (e.g., `Sp1`). The authors already studied vertical bat-fruit networks; the standard conditional MI decomposition + fixed-margin null is an exploratory analytical framing, not standalone ecological novelty.

**Main research state:** ODSP now has an independently authenticated functional 3-axis *observed interaction* example that complements the two-source acoustic detected-layer evidence in [separate Draft PR #306](https://github.com/zuizui0223/odsp/pull/306). The stricter target, **latent ecological intensity `λ(species,x,y,z,t)` with source-specific q and independent-site heldout predictive superiority**, remains **not identifiable/tested** from these pooled stratum matrices. Future source discovery still needs same-site/time matched genuine height observations, independent site/year identifiers and effort/detection anchors. No switching datasets to obtain a desired positive branch outcome is warranted.
