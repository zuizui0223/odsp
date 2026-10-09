# Valid reference calibration is not enough when the target passage mix differs

**Source-free follow-up to PR #251; the original #251 nulls and results
were inspected before this new reference sampling was frozen.**

The parent construct had a known problem: a fixed n near reference
sample and n far reference sample are non-identically-distributed
Bernoulli trials with detection q_near=.9 and q_far=.3. Applying a
naively pooled Binomial(2n,p) Clopper-Pearson model to the sum is
not a calibrated binomial procedure even at the reference source,
in addition to being invalid for the target animal distance mix.

This independent v1 fixes that FIRST flaw while preserving the
biologically relevant SECOND flaw (population transport):

- For each reference passage, independently choose near/far with
  probability .5/.5. Given near/far, trigger success probability is
  .9/.3, and opportunity labels are independent and correct.
- Every observed focal trigger across those IID opportunities is
  **exactly IID Bernoulli(.6)** after integrating reference passage
  distance. The total reference successes are now genuinely
  Binomial(2n,.6) for each season×solar bin. Exact 4-cell CP with
  joint calibration alpha=.025 is mathematically legitimate on
  THIS reference population.
- Under the seasonally mixed target animal passage proportions
  (.2,.8,.8,.2), true target detection q is instead
  (.42,.78,.78,.42): seasonal detector OR=3.44898 even with
  constant distance-specific detector response.
- All original source-free animals and the fully corrected external
  8-q + 4-target-mix calibration from #251 are reused with the
  EXACT original RNG, and every corrected first-result frequency
  is replay-locked to the parent terminal ledger. The new truly IID
  reference detector q samples use an independent RNG stream
  `SeedSequence([2026100916, wi, ni, rep, 734])`.

The source q confidence intervals may have excellent coverage
for q_reference=.6 yet be irrelevant to q_target. A positive
seasonal animal inference on q_reference is then a mistake of
**external validity/transport**, not an incorrect CP interval
coverage calculation.

This test preserves all 4 ecological truth worlds (balanced mix,
confounded mix with animal OR1, reversed mix, genuine animal OR2
plus confounded mix), all three original n=50,200,1000
q-calibration sizes and 200 synthetic replicate paired worlds each.
The valid IID source calibrator uses 2n truly IID reference passage
trials PER original season×solar bin (8n total); the fully target
standardized route uses 8n q reference passages PLUS 4n separate
target-distance mix opportunities. These are not identical external
measurement budgets; the result is a *transport failure check*,
not equal-cost calibration method effectiveness.

Practical ecological consequence: one cannot claim animal seasonal
photoperiod reorganization from clock/phase detection timings even
with extremely accurate detector q calibration unless calibration
opportunities cover the same distribution of passage distances,
angles, speeds, species and occlusion as the TARGET season×phase
animal encounter opportunities, or those characteristics are
independently measured and properly standardized.

NO original NIE EcoBank operation records, field camera q
reference trials, animal detections or protected coordinates
have been accessed. Previous ODSP inferred terminals and primary
process routes are unchanged.
