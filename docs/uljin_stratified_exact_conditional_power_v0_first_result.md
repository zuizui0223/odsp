# Post-outcome readout: exact site-stratified size and power

**STATUS: POST-RESULT descriptive readout; NOT a new preregistered method.**
These numbers are transcribed from the **first complete archived result** of
PR #243, not recomputed under modified conditions.

- Frozen pre-outcome contract commit: `45b63c3d`.
- First attempted CI `37796470299`: stopped during tests, before scoring.
  Fixed only float tail probabilities overflowing 1 by a few ulps
  (`71fd705d`), with a fail-closed tolerance.
- First **completed** full 48-point panel:
  [GitHub Actions 37796638655](https://github.com/zuizui0223/odsp/actions/runs/37796638655);
  artifact `11559300590`,
  SHA256 `7a344da2929572268f124d461cea74687748c482924fe468adc159816142a8bc`.

## Exact synthetic finite-sample comparisons

Every probability below is calculated analytically from predeclared
within-physical-site fixed hypergeometric margins, **not Monte Carlo**.
The last two columns are stratified exact conditional power for a common
true within-site early-vs-late season odds ratio of 2 or 3.

| Fixed-margin family | Physical sites | Total synthetic detections | Stratified null rejection | Naively pooled actual null rejection | Stratified power OR=2 | Stratified power OR=3 |
|---|---:|---:|---:|---:|---:|---:|
| Sparse balanced | 2 | 8 | 0.02778 | 0.02778 | 0.09467 | 0.16736 |
| Sparse balanced | 4 | 16 | 0.01312 | 0.01312 | 0.08067 | 0.17738 |
| Sparse balanced | 8 | 32 | 0.01484 | 0.06005 | 0.15239 | 0.35938 |
| Sparse balanced | 16 | 64 | 0.02481 | 0.06334 | 0.36282 | 0.72145 |
| Moderate balanced | 2 | 40 | 0.01387 | 0.01387 | 0.14125 | 0.33469 |
| Moderate balanced | 4 | 80 | 0.02391 | 0.02391 | 0.34852 | 0.70094 |
| Moderate balanced | 8 | 160 | 0.04439 | 0.04439 | 0.70684 | 0.96721 |
| Moderate balanced | 16 | 320 | 0.03170 | 0.05074 | 0.90591 | 0.99918 |
| Composition confounded | 2 | 160 | 0.02117 | **1.00000** | 0.22476 | 0.50439 |
| Composition confounded | 4 | 320 | 0.03084 | **1.00000** | 0.45889 | 0.83311 |
| Composition confounded | 8 | 640 | 0.02746 | **1.00000** | 0.70785 | 0.97966 |
| Composition confounded | 16 | 1280 | 0.03679 | **1.00000** | 0.95184 | 0.99992 |

**The site-conditioned exact null never exceeds 0.05** in these cases.
The invalid pooled comparator can exceed 0.05 even when every site's
within-site OR is truly 1. Its `1.00000` is an artificial, fixed-margin
Simpson extreme, **not a real-data false-discovery rate**. Some
pooled-null values >0.05 are also possible with identical site margins,
because the site-conditioned sampling law is not the pooled Fisher null.

## Same observed synthetic detections, different questions

- Early-profile site: rising (early,late)=(18,2);
  falling=(54,6). Within-site OR=1.
- Late-profile site: rising=(6,54); falling=(2,18).
  Within-site OR=1.
- Pooling yields OR=5.44444 and one-sided Fisher p=3.45889e-7.
- Original-site-conditioned exact one-sided p=0.60344321.

The site-conditioned contrast answers whether the **within-site detected
season×bin odds ratio** exceeds 1 under the fixed margins. The pooled
contrast instead responds to the sampling composition and becomes
unreliable for within-site ecology when time-of-day profiles co-vary
with seasonal detection rate.

## Practical admission gate

These artificial site counts and event totals DO NOT imply that the
Uljin 2022 mirror dates have corresponding independent observations;
the 4,623 published detections cover the full source year and four taxa.
Nor does correct inference on detected-event odds automatically
separate animal activity from camera detection efficiency. A real
validation requires independent source-operation intervals, source
timestamp timezone and station identities, frozen response-independent
site×date-pair roster, and preselected phase-bin contrast. A new
empirical hypothesis test must be independently preregistered;
this synthetic test does not qualify prior or primary ODSP routes.
