# Site-conditional exact test: protecting within-site behavior claims from pooling

**Scope:** synthetic fixed-margins conditional inference, not ecological
field data. This follows ideal balanced one-site Fisher power (PR #242).
We now admit heterogeneous station-specific occurrence profiles, unequal
branch frequencies and sparse site margins, *conditionally* and exactly.

For each physically distinct synthetic site i, observe totals N_i over
two preselected solar-phase bins and two rising/falling branches, with
K_i=early bin total and D_i=falling branch total. Holding these fixed,
X_i=(falling, early) has a central hypergeometric null distribution:
P(X_i=x | N_i,K_i,D_i, theta_i=1) =
C(K_i,x) C(N_i-K_i,D_i-x) / C(N_i,D_i).

No assumption that all sites have the same baseline activity shape or
overall falling-vs-rising rate is needed under this null. Assuming
site-conditioned sampling is independent between physical sites, the
site-stratified T=sum_i X_i null distribution is the exact convolution
of individual hypergeom laws. A *common* within-site conditional odds
ratio theta under an alternative gives the exponential tilt
P_theta(T=t) ∝ P_1(T=t) theta^t. This yields **analytic, not Monte
Carlo**, conditional size and power for the preselected one-sided
theta>1 target.

The intentionally invalid comparison collapses all site×season×bin
margins into one 2×2 table and applies Fisher's central hypergeom
test as though sites had a common observation rate structure.
Its apparent nominal p-values are not calibrated conditional on
site-specific margins when phase profiles correlate with seasonal
branch-rate shifts. We evaluate that test's ACTUAL rejection probability
under the same exact site-conditional null. Pooled events are **not**
independent physical sampling units.

## Frozen design
- Templates: sparse balanced (N=4,K=2,D=2/site), moderate balanced
  (N=20,K=10,D=10/site), and paired compositional-confound sites
  (type early N=80,K=72,D=60; type late N=80,K=8,D=20).
- Site counts R=2,4,8,16, with equal numbers of the compositional types.
- True common conditional odds ratios theta=1,1.5,2,3. Each of the 48
  fixed scenario points is reported without selection or retuning.
- A concrete witness has early site (rising early/late 18/2,
  falling early/late 54/6) and late site (rising early/late 6/54,
  falling early/late 2/18). BOTH site-specific odds ratios =1;
  pooling yields a non-unit association.

This targets a **detected-event** early-vs-late odds ratio, not latent
animal activity. It is a conditional repeated-sampling thought
experiment with fixed *observed* row/column margins; it does not
tell how frequently actual sparse sites achieve these margins or
how many independent field stations must be deployed to get them.
No original data, operator logs or GPS accessed. Unequal/subdaily
camera exposure and season-bin-specific detection efficiency would
invalidate applying this directly to biological activity. This is
not a six-bin global search, and it does not qualify or revise
primary ODSP inference routes.

A good downstream original-source workflow would authenticate
source-independent camera uptime; freeze site roster independent of
detections; then tabulate site×matched-date pair×season×preselected
phase-bin counts including true zero-detection positive-effort cells.
For sparse/no-overlap sites, the exact conditional test may have
very low or zero attainable rejection probability. It must report
conditional support and effective number of physical sites, never
just sum of detection events.
