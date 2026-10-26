# BOP_RODENT: new-individual predictive gain envelope (method v1)

## Purpose and scientific boundary

A mean positive held-out score gain does not answer whether a **future independently
tagged individual** would also gain from using a richer ecological-state predictor.
GPS fixes are autocorrelated, and thousands of fixes from one animal are *not*
thousands of independent predictions about generalization to new animals.

ODSP already reports the frozen BOP_RODENT primary outcome (27/30 individual RF
log-score gains positive, 30/30 Brier improvements, all-individual terminal
**mixed**), the pooled-to-species-vs-context score decomposition, a four-species
small-cluster mean interval, and ordinary row-level split conformal sets. This
new method targets something else: a **one-sided predictive lower bound on a
future *group-average score gain***, with the independent group as the rank unit.

Implementation: odsp.new_group_gain_envelope.fit_new_group_gain_lower_envelope.
Read-only archived-data demonstration:
scripts/audit_bop_new_group_gain_envelope.py.

## Method

Let G_1, ..., G_n be **one precomputed held-out mean score gain per calibration
individual**, always with the same declared model, comparator, score orientation
and group definition. The scorer/model must be fitted without using those
calibration outcomes.

For a requested one-sided miscoverage alpha:

- k = floor((n + 1) * alpha).
- If k = 0, report a **vacuous -infinity lower bound**; do not fabricate a
  finite lower limit by taking a quantile at the calibration minimum.
- If k >= 1, L = k-th *smallest* calibration group gain.
- Under exchangeability of the n calibration group *scores* and the future
  group's score, P(G_new >= L) >= (n + 1 - k)/(n + 1) >= 1 - alpha.
  The inequality is conservative under ties.

If L > 0, it gives a conditional-on-the-assumptions marginal statement that a
new independent group's *mean gain* should exceed zero at the stated coverage
level. It is not a claim that every future group or every event gains. It is
not a confidence interval for the population mean gain or a simultaneous
all-groups positive certificate.

**Critical qualification:** exchangeability is a scientific/design assumption
that software cannot test from gain values. A single frozen predictor scored
on exchangeable independent groups can meet this design, provided group
sampling, admission and comparator roles are defensible. Merely obtaining
cross-validation scores does not establish exchangeability with the gain of
a *new predictor fit on the whole dataset*.

The interface requires unique group IDs and rejects nonfinite gains, but
cannot independently prove group independence, chronological model freezing
or sampling exchangeability. Two explicitly separate declared source roles
are exposed:

- fixed_predictor_groups: conditional rank statement **only if** independent
  group-score exchangeability is externally justified.
- historical_crossfit_descriptive: no formal future-group coverage claim.

The source design is part of the output, and every output says that
exchangeability was **not verified by software**.

## Read-only BOP_RODENT result

The frozen primary RF terminal receipt contains thirty individual gains, scored
under five deterministic group-fold models, plus a four-species roster. The
source training folds overlap; the four species are heterogeneous. Neither
all-thirty pooled score exchangeability with a future deployed RF, nor
species-conditional exchangeability with such an RF, is established.

Therefore the following are **descriptive rank stress tests of the archived
scores, NOT prospective conformal coverage certificates for BOP_RODENT**.

| BOP archived group-gain roster | n animals | k at alpha=0.10 | Descriptive 90%-rank lower | k at alpha=0.05 |
|---|---:|---:|---:|---:|
| All four species pooled (heterogeneous) | 30 | 3 | -0.026803 nats/event | 1; lower -0.230782 |
| Buteo buteo | 5 | 0 | vacuous (-infinity) | 0; vacuous |
| Circus aeruginosus | 8 | 0 | vacuous (-infinity) | 0; vacuous |
| Circus cyaneus | 8 | 0 | vacuous (-infinity) | 0; vacuous |
| Circus pygargus | 9 | 1 | +0.982395 nats/event | 0; vacuous |

Positive point gains in 27/30 animals do not rescue the pooled lower bound's
negative sign. Nor can the 5/5 observed positive Buteo gains supply a finite
one-sided 90%-rank bound from only five groups. The positive C. pygargus rank
bound reflects nine observed positive cross-fitted scores; **it is not 90%
future-species coverage**. No terminal category, model, bin, fold, admission
criterion, comparator or prior receipt is modified.

The BOP comparator is the **training-fold pooled altitude-state marginal**.
The present rank audit is about that original gain, *not* necessarily about
within-species context. The earlier descriptive species-baseline amendment
found 23/30 positive within-species context increments and negative mean
within-species context gain for Buteo. These distinct estimands must not be
collapsed into a new generic "environment predictive" conclusion.

## Reproduce

~~~bash
python -m pytest tests/test_new_group_gain_envelope.py tests/test_bop_new_group_gain_envelope.py
python scripts/audit_bop_new_group_gain_envelope.py
~~~

The script reads only BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json,
validates the frozen contract/terminal/primary gain roster and checks the
per-species gains against the exact total gain multiset. It emits standards-
compliant JSON (vacuous lower bounds are represented as null). Source
individual identifiers are neither available nor generated; script-internal
receipt-position labels are explicitly **not animal identities**. Output is
separate from and cannot overwrite the frozen receipt.

## Known-truth and next genuine deployment validation

Unit tests enumerate all twenty possible future-group ranks under the
exchangeable distinct-score world at alpha 0.10: exactly 18/20 cover, the
finite-sample target. An adversarial pseudoreplication test rejects using
10,000 records from one animal to turn two independent animals into 10,001
independent group scores. Additional tests cover ties, insufficient n,
malformed input, repeated identifiers, future-group reuse and frozen-receipt
tampering.

For a *new formal BOP-related deployment endpoint*, independently specify
the animal admission and future target population, freeze one predictor and
one training baseline, reserve exchangeable new individuals for **calibration**
and an untouched **validation** set, and retain each individual's mean gain
as one calibration unit. Freeze the rank rule and provenance before outcome
access. The historical BOP cross-fit scores can motivate that design but
cannot automatically become its prospective calibration sample.

The method does not correct telemetry detection bias, height-above-MSL
semantics, changes of species composition or distribution shift. Those
remain separate ecological and measurement challenges.
