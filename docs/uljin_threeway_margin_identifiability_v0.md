# When aggregate seasonal activity cannot identify within-station change

**Scope:** a known constructive contingency-table counterexample applied
to the ecological estimand discussed in ODSP's source-free Uljin
camera-trap studies. It is NOT a new general identifiability theorem,
an actual Uljin result, or a proof that independent Poisson inference
fails when original station-identified event records exist.

## Claim carefully separated by observation level

Construct strictly positive complete count tables `A[s,b,k]` and
`B[s,b,k]` for site type s∈{early,late}, photoperiod branch
b∈{rising,falling}, and six solar-phase bins k.

World A (no within-site diel shape change):
- Early site: rising [48,6,6,6,6,6], falling [144,18,18,18,18,18]
- Late site: rising [6,6,6,6,6,48], falling [2,2,2,2,2,16].

World B uses a zero-margin 3-way checkerboard delta:
- Early rising: [+3,0,0,0,0,-3]; early falling: [−3,0,0,0,0,+3]
- Late rising: [−3,0,0,0,0,+3]; late falling: [+3,0,0,0,0,−3].

The three distinct **two-way count summaries** are IDENTICAL:
(1) site × branch, (2) site × phase, (3) branch × phase.
Both worlds have the same grand total. Yet under A each site's
falling/rising activity-rate multiplier is constant over bins (3 or
1/3); under B it is not. The 28×24 linear marginalization matrix has
rank 19; its five-dimensional nullspace is the classical
`(n_sites−1)(n_branches−1)(n_phase_bins−1)` three-way interaction
fiber. The explicit checkerboard delta belongs to that nullspace.

Under **independent Poisson cells**, if the released observational
product is ONLY aggregated branch × phase counts summed over sites,
the resulting independent Poisson probability distributions are
**exactly the same** in A and B, with KL divergence 0. A fitted model
based solely on that pooled table can never distinguish A from B,
no matter how many independent repetitions at the same aggregate
resolution. Full site×branch×phase observations have positive
Poisson KL divergence and therefore contain distinguishing information.

Important qualification: this exact probability-law equivalence does
NOT automatically extend to the JOINT distribution of all three
overlapping two-way margins observed repeatedly. For example, the
covariance between the (early-site × rising-branch) margin and the
(rising-branch × first-phase-bin) margin equals the common underlying
cell mean: 48 under A but 51 under B. Thus the complete pairwise
tables are an exact single-realization **linear reconstruction fiber**,
not a theorem that their full repeated-sampling joint distributions
are identical. Publishing the same two-way margins hides the
realized high-order table, but does not preclude more sophisticated
likelihood-based inference using a repeated multivariate experiment.

## Ecological measurement implication

A claim about **within-physical-station** seasonal activity
reorganization needs a response-independent physical-station identity,
matched-date-pair identity, two branch labels, solar-phase event bins,
and independently recorded positive camera uptime in the relevant
continuous intervals. Missing operation data cannot be transformed
into nondetections, and location/time sampling must not be selected
based on observed animal presence. A full four-way
station × matched-pair × branch × phase-bin operational frame is
preferable to publishing separate two-way aggregates.

The proof is *structural and ecological-estimand-specific* only.
Detection counts cannot distinguish animal activity from changing
detection probability without additional ecological assumptions.
Site-level random effects, partial pooling and strong priors can
produce predictions from aggregated data, but they cannot recover
the missing realized three-way interaction without information or
assumptions. Earlier qualified ODSP process/refit inference and
historical empirical terminals remain unchanged.
