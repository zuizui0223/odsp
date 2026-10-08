# The same released 2D margins permit both directions of within-site diel change

**Status:** distinct post-PR239 analytical exact-integer enumeration. The
pre-result freeze acknowledges that the parent world's 2×2×6 tables and
its first/last phase-bin perturbation have already been seen. This is
not a blind biological discovery or a general new identifiability theorem.

The observed summary consists of ALL THREE pairwise count margins of
one artificial realized station-type × branch × 6-bin count table,
**not the complete three-way table**. Hold these published counts fixed,
require all hidden cells to be strictly positive integers, and
enumerate every exact completion of the hidden 24 cells.

Writing `x_k = n[early, rising, k]`, the three other hidden cells in
each bin are forced by pairwise margins:

- `n[early,falling,k] = n[early,all_branches,k] - x_k`;
- `n[late,rising,k] = n[all_sites,rising,k] - x_k`;
- `n[late,falling,k] = n[late,all_branches,k] - n[late,rising,k]`.

The site×branch total also fixes `sum_k x_k`. So the first five
`x_k` can be enumerated within their exact positivity ranges, and
the sixth is determined. The original margin operator nullity is
five. Each candidate is checked against **all three** frozen two-way
margins with exact integer arithmetic.

Scientific target fixed for this successor: the early site's
first-vs-last phase-bin season odds ratio

  OR = (F_early,first / R_early,first) /
       (F_early,last / R_early,last).

OR>1 implies a *relative* early-vs-late increase in the falling branch,
OR<1 implies the opposite, and OR=1 means no first-versus-last change.
This is deliberately a specific partial contrast, not a claim to
characterize an entire diel density shape.

The result provides the exact minimum and maximum odds ratio over all
strictly positive integer completions and counts how many completions
have negative, zero or positive log OR. These are a **deterministic
identification region** conditional on exact released margins and the
chosen positivity constraint, NOT statistical confidence limits or a
posterior distribution. Completion count is NOT a model probability.

A positive/nonpositive conclusion cannot be determined from the
released two-dimensional counts if the feasible region contains
both signs. This is distinct from the earlier exact
*branch×time-only independent-Poisson distribution equality*.
In particular, the **joint repeated-sampling laws** of the three
overlapping two-way margins can contain covariance information;
we do not assert their statistical sampling distributions are equal.

For real ecological inference, preserve physical station × matched
date-pair × photoperiod branch × solar-phase event count and corresponding
original, response-independent operating exposure (including zeros).
The latter is necessary to distinguish observation effort from animal
detection. This exercise uses NO real Uljin animal or operation data.
All original ODSP results and qualifications stay unchanged.
