# How much supplemental information actually resolves the ecological contrast?

**Status:** source-free exact finite-integer release design, post-outcome
successor to PR #240. Not a new general theorem, data-collection power
calculation, empirical wildlife result, or statistical interval.

We start from the 2,723 strictly positive complete 2×2×6 integer
site-type×season×solar-phase tables consistent with ALL THREE previously
published 2D count margins. The parent identifies neither direction of
the early-site first-vs-last phase-bin seasonal odds ratio, nor a unique
hidden three-way table.

Now suppose the researcher can recover **additional original three-way
cell counts** for EARLY site type × RISING season at one or more of the
six already defined phase bins. Any released count is exact and
requires no new sample in this artificial completion problem. The
actual camera data have not been accessed and would need authenticated
site/source and effort provenance for these measurements.

Enumerate **all 64 subsets** of six available cells, including empty
and full. For every possible released-count outcome, group all hidden
full tables that generate it. Distinguish three targets:

1. **Sign of one early-site seasonal first/last-bin contrast:** group
   contains only negative, only zero, or only positive odds ratios.
2. **Exact numerical odds ratio:** group contains just one Fraction.
3. **Complete 24-cell table:** group contains just one hidden table.

A design is called *universally sufficient* if its target is identified
for EVERY possible release outcome over the original 2,723 candidates.
This is a worst-case combinatorial concept, not mean predictive accuracy.

The original 28×24 pairwise marginalization operator has rank 19,
nullity 5. Adding supplemental unique three-way cells can recover
the full table with five independent counts. The target-specific
OR and sign need not use all five: first and last bin early-rising counts
are enough, because original 2D margins determine the companion
early-falling counts in those same bins.

A one-cell query is not universally sufficient for the sign. It can,
however, settle the sign for SOME observed releases; report the exact
ambiguous outcome values and count of completions that remain
undetermined. Counting completions is a combinatorial audit; it
**does not define a prior probability of an outcome**. Sequential
queries would need a separate preregistered policy and verified cost
model to become a field sampling optimization.

## What remains separate

This answers information-grain questions about the **exact realized
integer table**, not how many stochastic camera detections one needs
for a particular confidence level. Sampling uncertainty, independent
operation-time exposure, heterogeneity in detectability, and
station-specific behavior are not modeled. Real ecological validation
must still predeclare the physical-site×date-pair×branch×phase
operational roster, including true recorded zeros; these cannot be
imputed from detection-derived operation dates.

All original ODSP training-process and untouched-external routes
remain untouched and prior v0 terminal results are not reclassified.
