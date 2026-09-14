# Refit-aware information-lattice certification

## Why this layer exists

A fixed information lattice answers whether held-out transfer depends on the order in which scientifically unordered information blocks are added. For example, the two admissible filtrations

```text
base -> species -> species+season
base -> season  -> species+season
```

can have different adjacent gains even though they share the same base and full predictor.

A second problem remains: those lattice edges may themselves depend on which upstream model refit produced the held-out scores. A favorable reference fit can therefore appear to support universal full transfer even when most refits support only one information order.

`odsp.refit_information_lattice.certify_refit_information_lattice` audits both sources at once.

## Required input

For every node of the complete Boolean subset lattice, provide an aligned score matrix

```text
[refit, held-out row]
```

with the same refit axis and the same held-out rows at every node. For `m` information blocks this requires `2^m` node score matrices and yields `m * 2^(m-1)` directed information-addition edges.

The method also requires:

- independent held-out group labels;
- explicit validation-block labels;
- optional row weights;
- explicit refit IDs;
- an optional reference refit ID for traceability;
- familywise confidence, draw count and minimum-support settings.

All non-full lattice nodes are comparators and must have finite score on every positive-weight row for every refit. The richest full node may contain `-inf`; a zero-support richest prediction is retained as predictive failure rather than smoothed away.

## Nested resampling

Each Monte Carlo draw has two aligned stages.

1. **Select one refit.** One supplied refit ID is selected and used for every independent group and every lattice edge in that draw.
2. **Resample validation blocks.** Within each group, validation blocks are sampled with replacement. The same sampled block indices are used for every lattice edge in that group.

This preserves the empirical dependence induced by using one upstream refit across the whole prediction system and preserves cross-edge covariance within each held-out group.

One studentized max-t critical value is then formed over the full estimable

```text
group × lattice-edge
```

family.

The result is therefore not a collection of independently corrected edge intervals.

## Four different summaries are kept separate

The output deliberately distinguishes:

1. **reference-fit point path status** — the ordinary lattice result for the declared reference fit;
2. **reference-fit certified path status** — validation-block certification conditional on that one reference fit;
3. **per-refit point path statuses** — how the complete lattice changes across supplied refits;
4. **refit-aware certified path status** — the joint refit/block result using the global group × edge max-t family.

A reference fit cannot override a coarser refit-aware conclusion.

The method also reports a refit-averaged point path status, but this is only a diagnostic of the empirical refit mixture. It is not interpreted as a synthetic biological predictor and cannot rescue a failed edge.

## Example: reference fit looks universal, refit-aware result does not

Consider two information blocks `A` and `B` with row-wise gains that are constant within validation blocks.

For the reference refit:

```text
base -> A   +0.60
A    -> AB  +0.30
base -> B   +0.01
B    -> AB  +0.89
```

Both admissible paths reach the full node.

For seven additional refits:

```text
base -> A   +0.60
A    -> AB  -0.20
base -> B   +0.01
B    -> AB  +0.39
```

Only the `base -> B -> AB` path remains positive.

The reference fit is therefore `universal_full_transfer`, but the refit ensemble is path-sensitive. Because the same selected refit is shared across all cells within each Monte Carlo draw, the refit-aware familywise result correctly stops short of claiming universal transfer.

## Interpretation boundary

The supplied refits form a **uniformly weighted empirical sensitivity ensemble**. ODSP does not:

- generate the refits;
- infer the refit scheme;
- assume that refits are independent samples from a population of models;
- divide their variability by `sqrt(R)`;
- choose a favorable refit after looking at held-out outcomes;
- choose the information order that gives the deepest transfer path;
- allow Shapley or refit-averaged summaries to override failed lattice edges.

The result answers:

> Does the claimed information-transfer path remain supported across the supplied upstream refits and held-out validation blocks, after simultaneous correction over all group × lattice-edge cells?

It does not claim to span all possible model uncertainty.

## Relation to other ODSP layers

```text
fixed single filtration
  odsp.information_transfer

refit-aware single filtration
  odsp.refit_information_transfer

fixed complete unordered lattice
  odsp.information_lattice

refit-aware complete unordered lattice
  odsp.refit_information_lattice
```

The last layer is the strongest only when the scientific design genuinely contains multiple unordered information blocks and a prospectively justified upstream refit ensemble. Otherwise the simpler layer is preferable.

## Computational scope

The complete lattice grows exponentially. With `m` information blocks, ODSP requires `2^m` subset predictors and audits `m * 2^(m-1)` directed edges. This is intended for a small number of scientifically meaningful information blocks such as species, site and season, not raw-feature attribution over dozens of covariates.
