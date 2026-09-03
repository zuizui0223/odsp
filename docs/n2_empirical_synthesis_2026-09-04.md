# N2 empirical synthesis — 2026-09-04

## The chapter-level result

The completed empirical programme does not support a binary statement that niches are either multidimensional or not. It supports a stronger decomposition:

1. an added axis may be structurally unestimable under a frozen observation architecture;
2. when estimable, the added axis may carry substantial descriptive thickness;
3. the detailed organization of that thickness may or may not generalize to prospectively independent data.

The three completed lanes occupy three different states of this decomposition.

| Lane | Added-axis thickness | Conditioned organization | Independent transferability | Terminal state |
|---|---|---|---|---|
| Tawaki | unavailable | not opened | unavailable | `empirical_gate_d_unavailable` |
| European free-tailed bat | present: ~4.02 effective z states | `P(z|x,y)` tested | 2/2 gains <= 0 | `empirical_n2_thickness_not_generalizing` |
| Snapshot Serengeti | present: ~5.15/6 effective t states | `I(Species;T|Site)=0.2243`, p=0.005 | 3/3 gains > 0 | `temporal_partition_generalizing` |

The machine-readable source for this matrix is `N2_EMPIRICAL_STATE_MATRIX.json`.

## What the contrast establishes

The bat and Serengeti results make the central methodological distinction empirical.

The bat support is vertically thick after x-y is known, yet the fine x-y-conditioned z distribution performs worse than the marginal z distribution in both sealed individuals. Thickness magnitude therefore does not imply transferable organization.

The Serengeti support is temporally broad after site is known, species identity partitions detected time within site beyond the within-site permutation null, and species-conditioned temporal organization improves held-out prediction in every one of the three cross-fitted site folds. Transferable organization can therefore occur under the same general N2 logic.

The strongest chapter-level statement is consequently:

> **Projection loss has at least two empirically separable components: how much added-axis state remains after projection, and whether the organization of that added state transfers to independent observations.**

This is stronger and more defensible than treating a large conditional entropy, a multidimensional fitted model, or a visually rich state map as sufficient evidence for a generalizable multidimensional niche.

## What the contrast does not establish

The bat and Serengeti systems differ in organism, observation process, added-axis semantics, conditioning variables and sampling architecture. Their numerical information values are therefore not a controlled test of whether time is biologically more generalizable than height.

The cross-lane contrast supports **existence of distinct empirical states**, not a causal explanation for why the lanes differ.

Likewise, the positive Serengeti temporal result does not reopen the vertical Gate-E forest-versus-grassland idea. That hypothesis concerns structural vertical capacity and requires its own separately frozen measurement architecture.

## Recommended Results structure

A manuscript can report the empirical results in the order of the inferential hierarchy rather than in dataset order:

1. **Estimability is itself an outcome.** Tawaki demonstrates that a prospectively defined multidimensional claim can fail at the observation-architecture gate without becoming a biological null.
2. **Thickness can survive projection.** The bat lane shows substantial vertical information hidden by x-y projection.
3. **Thickness is not enough.** The same bat lane fails independent transfer of its detailed x-y-conditioned vertical organization.
4. **Transferable organization is possible.** The Serengeti lane shows broad temporal thickness, detected species-time partitioning and positive transfer in every held-out site fold.
5. **N2 and N3 remain distinct.** Even the positive Serengeti terminal summary does not become an N3 state map without an integrity-pinned axis-resolved artifact.

## Recommended core figure

A compact four-panel figure would make the logic visible:

- **A — projection concept:** `S(x,y,z,t,...) -> S(x,y)` with lost-state information labelled by conditional entropy;
- **B — bat:** `H(Z|X,Y)=1.392`, `exp(H)=4.02`, two negative sealed gains;
- **C — Serengeti:** `H(T|Site)=1.640`, `exp(H)=5.15`, `I(Species;T|Site)=0.224`, p=0.005, three positive fold gains;
- **D — state matrix:** unavailable / thick-non-generalizing / thick-generalizing as distinct terminal states.

Panel D is the conceptual payoff: it prevents readers from reducing the chapter to a claim that “adding dimensions improves models.”

## Claim ceiling

The synthesis supports a general inferential framework and two contrasting empirical examples. It does not establish a universal frequency of each state, a causal mechanism for cross-system differences, or direct equivalence between vertical and temporal ecological dimensions.
