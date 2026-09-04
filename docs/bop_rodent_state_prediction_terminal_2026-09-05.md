# BOP_RODENT state-resolved prediction — terminal result

## Status

Primary terminal category: **`empirical_state_prediction_mixed`**.

The public BOP_RODENT v3 endpoint was prospectively frozen before GPS outcome access in `BOP_RODENT_STATE_PREDICTION_CONTRACT.json`. The contract fixed the source version and checksums, four absolute-altitude bins, 60-minute thinning, individual/species admission rules, deterministic individual folds, species/individual weighting, primary random forest, multinomial-logit sensitivity, metrics, and the all-individual sign rule.

No retuning was performed after outcome access.

## Data flow

The three checksum-pinned 2020–2022 GPS files contained **1,988,907 raw rows**. After the frozen complete-case/range filters, **1,983,483** events remained; hourly thinning retained **158,586** events. Final admission yielded **154,655 events from 30 individuals and four species**:

- *Buteo buteo*: 5 individuals;
- *Circus aeruginosus*: 8 individuals;
- *Circus cyaneus*: 8 individuals;
- *Circus pygargus*: 9 individuals.

*Asio flammeus* did not meet the frozen individual/state admission rule and was not used for transfer scoring.

## Primary random-forest result

For each held-out individual the primary score was

\[
G_j = E_{\text{heldout},j}[\log P_{\text{train}}(A\mid X, species)-\log P_{\text{train}}(A)],
\]

where `A` is the fixed four-state absolute-altitude target and the comparator is the training-fold marginal altitude distribution.

Results:

- **27/30 individuals** had positive primary log-score gain;
- **3/30** had non-positive gain;
- mean gain (descriptive only): **+0.5709102207418053 nats/event**;
- median gain: **+0.39577484343945035**;
- range: **−0.23078224313265183 to +1.499987587497081**;
- multiclass Brier improvement was positive for **30/30 individuals**;
- mean Brier improvement: **+0.3349841597067561**;
- mean top-1 accuracy: **0.7562012255655401**;
- mean probability assigned to the realized altitude state: **0.6483575293928328**.

The frozen all-individual rule therefore yields **mixed**, not generalizing. The positive mean cannot rescue the three conflicting held-out individuals.

### Species-level descriptive categories

- *Buteo buteo*: **generalizing**, 5/5 positive, mean gain +0.2303113866257108;
- *Circus pygargus*: **generalizing**, 9/9 positive, mean gain +1.2461295036462299;
- *Circus aeruginosus*: **mixed**, 7/8 positive, mean gain +0.34952380081933204;
- *Circus cyaneus*: **mixed**, 6/8 positive, mean gain +0.24554921871936009.

These species categories are secondary and do not override the all-individual terminal category.

## Multinomial-logit sensitivity

The frozen standardized multinomial-logit sensitivity gave positive log-score gain for **22/30 individuals**, with mean gain **+0.08617505942626986**. *Buteo buteo* and *Circus pygargus* again had all-positive species-level gains; the two other *Circus* species remained mixed. The sensitivity model cannot override the primary RF terminal state.

## Interpretation

The endpoint supports a stronger use case than projection-loss diagnosis alone: a species-aware context model can predict a **distribution over ecological altitude states** for independent tagged individuals, and that richer prediction outperforms a lower-information training marginal for most held-out individuals. The result also shows why ODSP keeps independent groups separate: strong average predictive improvement can coexist with genuine individual-level transfer failures.

The endpoint does **not** establish height above ground, causal effects of temperature/time/geography/species identity, a fundamental niche, correction of GPS/tag bias, or universal transfer outside the admitted public dataset.

## Provenance

- contract merged before outcome access: main SHA `bab8e4a4942199288e02ca893590f5732bed26e0`;
- frozen execution workflow: `33897335554`;
- result artifact: `9946375169`;
- artifact digest: `sha256:49291cf0f2c90955fc23bdc702ccef1ef8b710ce100c8e338c5fc6b91388b8f7`;
- result JSON SHA256: `9e681852d1982e03d9a0696ce5b78c8f367bbffcc401bc54e9b62368a211499d`;
- canonical summary: `BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json`.
