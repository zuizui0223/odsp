# First-results ecological reading: detector calibration and new-site majority

**This is a post-first-result interpretation of the frozen and complete
source-free PR #258 panel. The original frozen contract and first workflow
output were not changed or selectively rerun. NO actual EcoBank wildlife
activity or camera-hour source is asserted.**

## Receipt and fixed significance

- Frozen contract commit: `cd78c8710caab3c4c7feda058ef06af99912fd06`
- First source-free complete workflow:
  https://github.com/zuizui0223/odsp/actions/runs/38014938577
- Full original 192-condition 16-site results: workflow artifact 11655159899,
  sha256 `c18c003c5ce9c015d704fe885f521fe1706cc5e1115e86d99c0062f03c81b717`
- Source joint q-calibration noncoverage alpha=.025. Four predeclared
  site-majority tests Bonferroni combined alpha=.025, per test .00625.
  Under correct source q temporal granularity, independent sites,
  independent representative true-passage references and fixed
  trained models, per selected design combined false certification
  by union bound <=.05. NOT across all 192 scenario choices.
- With 16 independent physical camera sites, *not 82 days or 96
  bins*, q-robust positives must be >=14 for exact
  Binomial(16,.5) one-sided p<.00625.

## The 24 certified cases among all 192 frozen source-free comparisons

For the genuine 4h-constant detector q world, four-hour-source
calibration certified the following model A > B majority outcomes:

| Synthetic animal truth | Precommitted pair A > B | External source reference budget(s) | Certified site-event counts (per site/day) |
|---|---|---|---|
| CLOCK fixed | Mean anchor > invariant solar phase | 251,904 and 1,007,616 | 20 and 200, all four |
| SUNRISE/SUNSET tracking | Solar phase > civil clock | 251,904 and 1,007,616 | 20 and 200, all four |
| SEASONALLY shifted solar phase | Solar phase > civil clock | 251,904 and 1,007,616 | 20 and 200, all four |
| SEASONALLY shifted solar phase | Solar phase + branch > invariant phase | 251,904 and 1,007,616 | 20 and 200, all four |
| SEASONALLY shifted solar phase | Solar noon > civil clock | 251,904 and 1,007,616 | 20 and 200, all four |

Twenty certifications come from these 5 pair×budget×event-level
patterns under 4h-constant q, using 82×6 source CP intervals.

At the **larger 1,007,616 externally labeled passage opportunities**
with valid 82×96 quarter-hour calibration, the other four
certifications were all the `solar_noon > civil_clock` pair in the
SEASONALLY shifted synthetic animal time truth, at BOTH animal
event-levels and BOTH actual detector q patterns (genuine 4h
constant or varying inside blocks). This is predictive ordering of
two fixed trained models, not proof that a solar-noon cue caused the
seasonal animal behavioral mechanism.

For the LOW 251,904 reference budget, fine 82×96 q calibration
had **zero** qualified site-majority certifications on BOTH detector
truths, despite independent source q familywise CP coverage in this
first artificial realization. For the higher budget, only 2 of 24
fixed-model pairs certified at each true detector temporal pattern
with fine 15min q intervals.

Every one of the 48 4h source-calibration cases when true q varies
inside those original 4-hour blocks is HOLD for 96bin target
inference, regardless of valid 4h MEAN source CP coverage or a
favorable nominal score.

## Why this differs from PR #257

The parent PR #257 sample log-score sensitivity intervals do not
directly establish a new-site population property. This v0 uses a
different estimand: for a new PHYSICALLY INDEPENDENT site and
the SAME date and detector population, is the probability that A
out-scores B greater than 1/2? Even after q source calibration,
many fixed-model pairs cannot meet the >=14 of 16 site threshold.

The sign test cannot show positive EXPECTED per-site mean
logscore, nor generalize to an unseen REGION, unseen date, a
different camera, a new taxon, or an independently measured animal
encounter/active-state process. q may vary among cameras and
site vegetation, violating this first synthetic shared q model.

A key methodological guard is that source confidence coverage is
NOT conditioned upon the synthetic true-q oracle; all decisions
are computed as if real true q is UNKNOWN, and occasional CP
noncoverage is already included in the error budget. This is
necessary for any eventual genuine ecological frequentist claim.

The **original EcoBank v1.1 ZIP and true animal event timestamps,
independently recorded hardware operation frame, physical station
anonymized roster and reference q true-passages have NOT been
materialized**. No real seasonal diel time, zeitgeber, latent
activity, or memory discovery is claimed. Older qualified ODSP
resampling and external-validation routes remain exactly as before.
