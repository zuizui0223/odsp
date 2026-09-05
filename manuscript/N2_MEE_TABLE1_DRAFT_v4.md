# Table 1. ODSP validation layers and terminal evidence

| Validation layer | Prediction/state target | Independent unit | Primary comparison | Key result | Terminal interpretation |
|---|---|---|---|---|---|
| Known-truth stable | discrete `P(A|B)` | replicate | conditional vs marginal log score | 128/128 positive at n=50, 250 and 1000; mean gain +0.300 at n=50 and +0.323 at n=1000 | expected generalizing regime recovered |
| Known-truth shifted | discrete `P(A|B)` | replicate | conditional vs marginal log score | 128/128 negative at all sample sizes; mean gain -0.782 at n=50 and -0.773 at n=1000 | precise fitted organization did not falsely imply transfer |
| Known-truth unorganized | discrete `P(A|B)` | replicate | conditional vs marginal log score | mean gain approached zero (-0.0094 at n=50; -0.00068 at n=1000) | no predictive information recovered when none existed |
| MH_ANTWERPEN | four-state absolute altitude `P(A|X)` | tagged individual | prospective minimum-individual gate before RF transfer | 193,370 thinned events but 3 eligible individuals vs frozen minimum 4; 0 RF folds | `empirical_state_prediction_unavailable` |
| BOP_RODENT primary RF | species-aware four-state absolute altitude `P(A|X,species)` | tagged individual | held-out RF log-score gain vs training marginal altitude distribution | 27/30 positive; mean gain +0.5709; 30/30 positive Brier improvement; mean top-1 accuracy 0.756 | `empirical_state_prediction_mixed` because 3 individual gains were non-positive |
| BOP_RODENT logistic sensitivity | same state target | tagged individual | held-out multinomial-logit gain vs training marginal | 22/30 positive; mean gain +0.0862 | sensitivity only; cannot override RF terminal state |
| Tadarida supporting diagnostic | vertical state conditional on horizontal location | sealed individual | `P(z|x,y)` vs marginal `P(z)` | 4.02 effective vertical states; both sealed gains negative | thickness present but organization non-generalizing |
| Snapshot Serengeti supporting diagnostic | time state within site/species context | held-out site fold | species-conditioned time vs lower-information comparator | 5.15/6 effective temporal states; all 3 site-fold gains positive | transferable temporal organization |

**Notes.** BOP_RODENT and MH_ANTWERPEN are the prospective state-prediction endpoints. Tawaki, *Tadarida teniotis* and Snapshot Serengeti are retained as supporting evidence for estimability, added-state thickness and transferability but are not additional training datasets for the new `P(A|X)` empirical prediction test. Mean gains are descriptive; terminal categories follow the prospectively frozen independent-group sign rules.
