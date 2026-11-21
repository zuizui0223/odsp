# Swiss red-kite: 12-cell proper-score sign-disagreement audit (source free)

## Scientific question and frozen boundary

The original Swiss red-kite 2020/2021/2022 calendar-forward design already scored 96 fixed-family `ranger` forests for home-range (HR) and nesting labels, with/without prior-training-bird purge. The **2021 primary source bird-ID-disjoint** result retained positive probabilistic gains, while 2022 (32 seasons with 32 distinct source bird-ID strings, only four negative seasons) had a low AUC and a negative **HR log-score gain**. A separate exact finite-rank diagnostic clarified why the 2022 below-half AUC is not proof of a real ecological regime change.

This follow-up is a *post-result interpretation*. Exploratory arithmetic had already identified the 2022 HR sign disagreement before commit **`b4e5cc679abd026a6748c62940efabd17defea5b`** froze `research/BOP_SWISS_PROPER_SCORE_DISCORDANCE_V1_CONTRACT.json`. That contract fixed the full twelve-cell scope and evidence limits before implementation and formal replay; it did not precede the first look at the anomaly or make this a confirmatory analysis. The replay reads **only the already published immutable aggregate** `BOP_SWISS_TEMPORAL_BIRD_PURGE_V1_FIRST_RECEIPT.json` (Git blob `82c328cc5bd5b88afa2faf8f0121d607af1a4e72`), and the 2022 exact-rank source-free receipt (Git blob `9896eb070a208b06b7d763b5a6e806a797e0fb37`). The original Swiss 2024 RDS, raw nesting labels, individual model probabilities, GPS or bird IDs are never reopened; no forest is fitted.

## Proper scores, with the **same pre-existing train-only reference**

For each of the **12 fixed year × response × training-mode cells**, the source receipt contains:

- `q`: proportion positive in the **training** seasons (training-only constant baseline probability).
- `π`: proportion positive in the already evaluated test seasons.
- `BS_model`: mean binary Brier error, `mean((p - y)^2)`, and `LL_model`: negative mean natural-log probability of the true binary outcome.
- `G_log`: original log-score improvement over the constant training-only prediction `q` (positive = better).

From these frozen **aggregate numbers alone**, we reconstruct

\[
BS_{\mathrm{ref}} = \pi(1-q)^2+(1-\pi)q^2,\qquad
G_{\mathrm{Brier}} = BS_{\mathrm{ref}}-BS_{\mathrm{model}}
\]

and audit the independent log identity

\[
LL_{\mathrm{ref}} = -\pi\log q-(1-\pi)\log(1-q),\qquad
G_{\log}=LL_{\mathrm{ref}}-LL_{\mathrm{model}}.
\]

The log identity agrees in all 12 cells within `1e-5` (six-decimal source rounding). **Both gains use a probability derived from training data only.** The test prevalence `π` is used to *score* that frozen reference, not to choose its value or to train it. This is not the test-label majority-class *oracle* of the previous rank/accuracy audit.

## Results: sign disagreement in exactly 2 of 12 cells

| Frozen temporal cell | HR/nest | Training mode | Brier reference | Brier model | Gain in Brier score | Gain in log score |
|---|---|---|---:|---:|---:|---:|
| 2020 | HR | all prior years | .280624 | .037978 | **+.242646** | +.504099 |
| 2020 | HR | bird-purged prior years | .332370 | .036055 | **+.296315** | +.662324 |
| 2020 | nest | all prior years | .266804 | .090544 | **+.176260** | +.368822 |
| 2020 | nest | bird-purged prior years | .309975 | .085944 | **+.224031** | +.553932 |
| **2021 primary** | HR | all prior years | .251875 | .054092 | **+.197783** | +.266383 |
| **2021 primary** | HR | bird-purged prior years | .253505 | .053654 | **+.199851** | +.267306 |
| **2021 primary** | nest | all prior years | .263045 | .117124 | **+.145921** | +.244245 |
| **2021 primary** | nest | bird-purged prior years | .265144 | .129345 | **+.135799** | +.225660 |
| 2022 | **HR** | all prior years | .250565 | .128858 | **+.121707** | **−.584100** |
| 2022 | **HR** | bird-purged prior years | .294236 | .127684 | **+.166552** | **−.609657** |
| 2022 | nest | all prior years | .332151 | .172999 | **+.159152** | +.168385 |
| 2022 | nest | bird-purged prior years | .389273 | .197332 | **+.191941** | +.184597 |

All 12 model panels improve the Brier error relative to their own **training-only** prevalence baselines. But **the two 2022 HR panels have negative log-score gain despite the positive Brier gain**. The 2021 primary year (both outcomes, both modes) remains concordantly positive.

This numerical disagreement is not contradictory mathematics: both Brier and logarithmic scores are proper, but logarithmic loss strongly penalizes very small probabilities assigned to observed outcomes. However, **we cannot conclude from cell-averaged scores alone that a particular extreme-probability failure caused the result**, nor can we locate the four negative birds, measure per-bird variability, estimate calibration curves, reconstruct the per-record score distribution or infer a mechanistic 2022 distribution shift. Within each cutoff, the same test rows underlie the eight seeds and both training modes; the 12 cells are not independent replicates. The purged arm establishes disjointness only of source bird-ID strings, without external canonical animal identity resolution. The post-result contrast is exploratory and contains no newly untouched source outcomes.

## What this changes in the method

A high AUC, high accuracy, or positive Brier improvement is **not sufficient** for the ODSP scientific claim that a state-resolved predictor improves a future animal's assigned-outcome probability under the prespecified log-score estimand. A model may pass the Brier skill check and fail the more tail-sensitive log-score check. We therefore retain **signed, reference-aligned log-score gain** as the separate primary estimand for BOP independent-animal methodology, while reporting Brier and AUC as complementary diagnostics **without cherry-picking the preferred outcome metric after inspection**.

This is a restriction on *what the existing 2022 retrospective scores establish*, not a new performance experiment or evidence that Brier is invalid. Original BOP `empirical_state_prediction_mixed`, original Dryad `NOT_ADMITTED`, and unqualified real red-kite external new-animal gain `HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER` are **unchanged**.

## Reproduce without any provider source access

```bash
python -m pytest -q tests/test_bop_swiss_proper_score_discordance_v1.py
python scripts/bop_swiss_proper_score_discordance_v1.py --out /tmp/bop-swiss-proper-score-discordance.json
```

The script rejects an output path that aliases the frozen contract or either input receipt, including relative paths, symbolic links and hard links. It then checks the contract and both prior receipts by Git blob hash, verifies each of all twelve source cells against the old majority-audit accuracy receipt, cross-checks the log-loss identity, and halts on tampering. CI runs under Python 3.10, 3.12 and 3.13 without R or external source downloads. The frozen replay specification, original result receipts and all biological STOP states are preserved.
