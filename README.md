# ODSP — Chapter 2: multidimensional niche geometry

ODSP is **Chapter 2** of the fixed four-chapter programme `niche-to-survey-four-chapter-v1`:

1. **SDMR** — which environmental dimensions define an interpretable realized niche?
2. **ODSP** — how thick and multidimensional is that niche beyond a flat x-y map?
3. **EOG** — which distributional/transition worlds remain possible and reachable?
4. **ACSP** — where should field effort be directed next?

See [`FOUR_CHAPTER_PROGRAM.md`](FOUR_CHAPTER_PROGRAM.md), [`CHAPTER_CONTRACT.json`](CHAPTER_CONTRACT.json), and [`CHAPTER2_ROADMAP.md`](CHAPTER2_ROADMAP.md).

## Scientific center

A conventional species-distribution product ultimately collapses support to a horizontal field:

```text
S(x, y)
```

ODSP asks what that projection discards. An ecological state can instead be indexed by additional axes:

```text
S(x, y, z, t, ...)
```

where `z` may represent canopy stratum, height, water/soil depth or another explicit vertical state, and `t` may represent observation/activity time, date or season when the source precision permits it.

The Chapter-2 question is:

> **HOW THICK is it? — How much ecological state-space information is lost when a multidimensional niche/support distribution is flattened to x-y?**

The working principle is: **地図は、niche を薄くする。**

## State-resolved ecological prediction

ODSP now extends beyond projection-loss diagnosis to predict **full ecological-state probability distributions** rather than only single-valued suitability outputs.  The common prediction targets are:

```text
P(A | B)   discrete/base-state prediction
P(A | X)   continuous-covariate prediction at new rows/locations
```

where `A` may be one or more added ecological states such as altitude layer, depth, time bin, phenophase, behaviour or microhabitat.  The package includes:

- a transparent Dirichlet-smoothed conditional reference learner;
- event-table encoding for public tracking, camera-trap and phenology data;
- optional scikit-learn probability-estimator bridges, including tested multinomial-logit and random-forest references;
- full per-state probabilities, dominant state, entropy/effective states and support diagnostics;
- held-out log score, Δ log score over a training marginal comparator, multiclass Brier score, top-1 accuracy and independent-group terminal classification.

The prospective BOP_RODENT public-data endpoint provides the first larger multi-species empirical validation of this prediction layer.  With the design frozen before GPS outcome access, 30 individuals from four admitted raptor species were independently evaluated.  The primary random-forest state model improved held-out log score over the training marginal altitude distribution in **27/30 individuals** and improved multiclass Brier score in **30/30**.  Under the deliberately conservative all-individual rule the terminal result is therefore **mixed**, not generalizing: *Buteo buteo* and *Circus pygargus* were species-level generalizing, while *Circus aeruginosus* and *Circus cyaneus* contained conflicting held-out individuals.  See [`BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json`](BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json).

This prediction layer does **not** turn ODSP into a new MaxEnt/RF-style occurrence algorithm.  Upstream learners can produce state probabilities and ODSP supplies a common ecological-state target, richer prediction output and independent scoring architecture.

## Niche thickness

`odsp.niche_geometry` provides model-agnostic information-theoretic metrics on any non-negative support distribution.

For horizontal axes `X,Y`, vertical axis `Z` and time axis `T`:

```text
vertical information      = H(Z | X,Y)
temporal information      = H(T | X,Y)
joint added information   = H(Z,T | X,Y)
```

The corresponding effective state counts are:

```text
vertical thickness        = exp(H(Z | X,Y))
temporal thickness        = exp(H(T | X,Y))
joint added thickness     = exp(H(Z,T | X,Y))
```

These quantities answer: **after horizontal location is already known, how many effectively distinct states remain along the added axes?**

`axis_thickness_map(...)` returns the same information separately for each supported x-y cell. A species-support tensor yields descriptive niche thickness; an explicitly defined availability/capacity tensor can instead represent structural state-space capacity. Those interpretations must not be mixed.

## Thickness magnitude versus thickness organization

The empirical results show why two distinct questions are needed:

1. **Thickness magnitude:** is added-axis state information present in a fitted support?
2. **Thickness organization / transferability:** does the detailed conditioned added-axis distribution remain useful for independent individuals, sites or observations?

A fitted support can be descriptively thick without its detailed organization generalizing. Conversely, a thick added axis can contain identity-resolved organization that does generalize.

`odsp.transferability` makes that distinction explicit and model-agnostic. For base state `B` and added state `A`:

```text
in-sample organization    = I(A;B)
held-out transferability  = E_heldout[log P_model(A|B) - log P_model(A)]
```

`base_added_mutual_information(...)` measures fitted organization. `score_conditional_transferability(...)` tests whether that organization predicts independent support better than the lower-information marginal representation. `classify_independent_gains(...)` and the grouped-transferability layer provide conservative all-positive / all-nonpositive / mixed decisions for prospectively independent held-out groups without allowing a large group to rescue a failed one. Cross-fitted grouped scoring permits each held-out group to have its own prospectively defined training model.

The transferability core deliberately performs no hidden smoothing. Any smoothing or pseudocount rule must be declared upstream before held-out outcomes are opened. Known-truth tests include thick but unorganized support, stable organization with positive held-out gain, and shifted organization with negative held-out gain.

## Temporal thickness versus temporal partitioning

Time is not treated as a special side analysis. It is an added niche axis with a separate identity-partition question.
