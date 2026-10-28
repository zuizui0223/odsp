# Technical note: one-sided future-animal gain bounds and their exact claim ceiling

**Status:** methods-paper derivation and assumptions audit, written **after** the frozen BOP method simulations. No theorem here is claimed as a new statistical discovery. The split-conformal/order-statistic principle is established (Angelopoulos & Bates 2023); the novelty, if any, is the *auditable ecological workflow and its negative source gates*, not the finite-sample rank lemma.

**Reproducibility inputs:** \`research/BOP_METHOD_PAPER_EVIDENCE_MATRIX_V1.json\`, frozen individual-gain receipts, \`odsp/new_group_gain_envelope.py\`, \`odsp/fixed_group_gain_protocol.py\`, \`odsp/managed_group_forecast_v1.py\`, \`odsp/group_identity_gate.py\`, \`odsp/identity_checked_transport.py\`.

## 1. Estimand: one future animal, not one future GPS event

Let \(\mathcal{F}\) denote the upstream training data, prespecified fitting procedure and any other information used to fix a state predictor \(q_{\mathcal F}\) and a reference \(b_{\mathcal F}\) **without observing any calibration or validation response**.

For a future biological animal \(j\), with telemetry rows \(r=1,\ldots,m_j\), prespecified positive weights \(w_{jr}\), observed discrete state \(A_{jr}\), and response-blind input \(X_{jr}\), define its *one* grouped log-score gain

\[
G_j = \frac{\sum_{r=1}^{m_j} w_{jr}\left[
\log q_{\mathcal F}(A_{jr}\mid X_{jr},s_j)-
\log b_{\mathcal F}(A_{jr}\mid s_j)
\right]}{\sum_{r=1}^{m_j}w_{jr}}.
\]

- \(s_j\) denotes the prespecified species/population stratum. Both probabilities must be positive for realized states.
- \(G_j\) is a **held-out individual mean log-score difference**; positive means the context-conditional predictive distribution assigns higher realized-state log likelihood *on that individual's observations* than the declared reference. It is not a causal environmental effect.
- The number of rows \(m_j\) does **not** become the number of independent replication units. Event-level dependence is allowed inside \(j\); the exchangeability requirement below is **between groups' scalar gains**, not between GPS fixes.
- Distinct IDs, even with different data-source prefixes, do not establish distinct animals. A canonical cross-source identity audit is a necessary provenance check, not mathematical proof of independence.
- The historic BOP random forest compared against the **fold-training pooled state marginal**. The newer managed common-input method compares against the **training-only species marginal**; the estimands are *different* and the 27/30 historic positive counts cannot be reinterpreted as conditional context gain beyond species.

## 2. One-sided rank lemma (known split-conformal construction)

Within a **fixed declared stratum**, suppose the calibration animal gains \(G_1,\dots,G_n\) and one new animal gain \(G_{\mathrm{new}}\) are exchangeable conditional on the frozen upstream training information \(\mathcal{F}\).

Let \(0<\alpha<1\), \(k=\lfloor(n+1)\alpha\rfloor\), and

\[
L_\alpha =
\begin{cases}
-\infty, & k=0,\\
G_{(k)}, & k\ge 1,
\end{cases}
\]

where \(G_{(k)}\) is the \(k\)-th *smallest* of the **calibration-only** group gains.

Then

\[
\Pr\{G_{\mathrm{new}}\ge L_\alpha\mid \mathcal F\}
\geq \frac{n+1-k}{n+1}
\ge 1-\alpha .
\]

**Proof.** When there are no score ties, conditional exchangeability gives a uniform randomized rank \(R_{\mathrm{new}}\) among the \(n+1\) group gains. The event \(G_{\mathrm{new}}<G_{(k)}\) can occur only if \(R_{\mathrm{new}}\leq k\), so its conditional probability is at most \(k/(n+1)\). For ties, applying random tie-breaking to define the rank preserves the argument and the **non-strict** coverage event \(G_{\mathrm{new}}\geq L_\alpha\) can only make the bound more conservative. If \(k=0\), taking \(L_\alpha=-\infty\) yields coverage 1 but no finite or positive guarantee. \(\square\)

**Precise sense of conditioning.** The guarantee may be stated conditional on a prespecified, response-independent upstream model/training sigma-field **for which the calibration and future gains remain conditionally exchangeable**. It is **not generally conditional on the realized calibration gains**, not automatically conditional on every realized holdout-feature roster, not guaranteed for every fitted predictor/calibrator or study cluster, and not unconditional evidence for an unverified source. Freezing artifacts and hashes checks *immutability*, not the substantive stochastic assumption.

At \(\alpha=0.10\):

| Calibration animals in a single stratum | Rank \(k\) | Conservative lower coverage, if exchangeable | Claim |
|---:|---:|---:|---|
| \(n=8\) | 0 | 1.0 for \(-\infty\) | **Vacuous** — do not produce a finite limit |
| \(n=9\) | 1 | \(9/10=0.90\) | First finite lower limit possible |
| \(n=19\) | 2 | \(18/20=0.90\) | Finite lower limit possible |
| \(n=30\) | 3 | \(28/31\approx0.9032\) | Only if these are valid calibration animals for one frozen deployed model |
| \(n=39\) | 4 | \(36/40=0.90\) | Prespecified synthetic target-source calibration |

Thus even nine calibration birds require **at least one different future bird** to examine untouched validation. There is no post hoc pooling across species in the existing method.

## 3. What this guarantee does and does not entail

**Relation to hierarchical conformal prediction:** Dunn, Wasserman
& Ramdas (2023) develop distribution-free prediction procedures for
new observations from hierarchically organized groups. Here the
scalar response to be covered is **the mean scoring advantage for one
whole independently sampled animal**, not the altitude state of
one new GPS record inside that animal. We do not propose or certify a
hierarchical row-level prediction set or a novel rank theorem.

1. If \(L_\alpha>0\) and the assumptions hold, then \(\Pr(G_{\mathrm{new}}>0\mid\mathcal F)\ge 1-\alpha\) for **one** future animal in that stratum. If \(L_\alpha\le0\), coverage of the lower bound does **not** establish positive gain.
2. There is **no guarantee that all** future individuals improve, no confidence interval for average population gain, no mean effect-size significance test and no biological causal claim.
3. Source-trained \(q_{\mathcal F}\) may perform badly on a target-source population yet the rank coverage remains valid **if calibration and future scores are still exchangeable within that target population**. Calibrating on target-source groups is not the same as showing that the predictor itself transfers well.
4. If calibration target and later validation target have different gain distributions, the rank conclusion may fail. Counterexample: all nine calibration gains equal \(+1\) and the new gain always equals \(-1\). Then \(k=1\), \(L_\alpha=+1\) and coverage is zero.
5. **Within-study/group dependence** may violate exchangeability of entire group gains even if individual identities do not overlap. Recorded study-cluster counts and canonical identity crosswalks cannot establish target-process exchangeability.
6. The same threshold applied to **many** validation animals yields marginal one-at-a-time coverage under assumptions, but its empirical fraction is correlated via the common trained model and calibration threshold. Reporting a binomial \(n=\) total animals interval as though independent across *retrained worlds* is pseudoreplicated precision.

These limitations are consistent with the general conformal literature and established distribution-shift caveats (Tibshirani et al. 2019; Barber et al. 2023; Gibbs et al. 2025).

## 4. Source/model/identity proof obligations

The statistical lemma is only one component of a credible ecological implementation. The software has separable checks:

| Obligation | Observable software evidence | Not established by that evidence |
|---|---|---|
| **Fitted model truly precedes responses** | Training-source hash, model/reference artifact hashes and deterministic source-to-model replay | Chronological human access to future biological response values |
| **Outcome-blind predictions are really from the model** | Re-evaluate all calibration and validation probabilities from the exact serialized model/reference artifacts | Authenticity of the original tracking provider |
| **One group is one biological animal** | Exact plan group roster, unique caller-supplied canonical animal keys across source/deployments | Truthfulness/completeness of an external identity crosswalk; ecological independence |
| **A nonvacuous bound can exist** | Within-stratum group counts, \(k\ge1\), at least one untouched test animal | Exchangeability of calibration/future gains |
| **The bound is not changed after calibration** | Frozen plan hash and calibration digest rechecked before validation scores | Real-source shift, unmeasured observational bias |
| **Source datasets have compatible semantics** | Exact required columns, UTC/coordinate resolution, target and state definitions, source version and licensing | Comparable ecological populations or observed predictor skill |

If **any** gate is unresolved, classification must stop at a source, identity, rank or evidence **HOLD**, rather than silently changing the model, pooling strata, imputing missing historical RF predictors or promoting the old \`mixed\` result.

## 5. Known-truth evidence already frozen

The code paths and outcomes are preserved in the evidence matrix and their original receipts:

| Method stage | Independent synthetic validation groups per scenario | Same-process target coverage | Adversarial validation-only shift coverage |
|---|---:|---:|---:|
| Frozen predictor + independent animal rank (#274) | 40,960 | 0.899438 | 0.068091 |
| Training-source-to-artifact-to-forecast replay (#275) | 10,240 | 0.891504 | 0.128711 |
| Reduced common-feature training + target-source calibration (#278) | 2,880 | 0.902431 | 0.262847 |

These scenarios were separately prespecified. Their different simulated learners, amplitudes and test generators mean they are **not three repeated estimates of one ecological effect**. The shifted-label scenario is intentionally adversarial, not a stochastic robustness guarantee. The latest identity-checked integration (#279–#280) tests executable consistency, not a fourth positive coverage benchmark.

The post-result descriptive world-level Monte Carlo audit of the 24-world common-feature experiment yielded equal-world stable coverage 0.90243 with approximate 95% Monte Carlo interval **[0.88614, 0.91872]**. Each of the 24 worlds had 120 test animals sharing model and calibrator. This t interval describes numerical uncertainty of the **retrained-world simulation mean**, not the 90% future-animal lower prediction bound.

## 6. Natural data gates and scientific stop rule

- Historic BOP_RODENT v3: 30 birds from four species, 154,655 retained fixes, 27/30 RF log-score positive and 30/30 Brier improvement positive. By the frozen all-individual criterion the terminal is \`empirical_state_prediction_mixed\`; historic cross-fit scores are **not** calibration scores for a single future deployed predictor.
- Same-study BOP 2026 public metadata: ten new candidate IDs dispersed among taxa, at most six in one species. This is insufficient for nine new calibration plus one untouched new test bird *within a species*; terminal remains \`NO_WITHIN_STRATUM_NEW_GROUP_RANK_SUPPORT\`.
- Independent Schaub 2026 Dryad: original RF requires an external-temperature predictor absent from the documented source and the spatial coordinate precision differs. There is no verified biological ID crosswalk; original-RF external evaluation remains \`NOT_ADMITTED\`. New managed reduced-input learner was tested on **synthetic** source-specific schemas, not actual Dryad GPS outcomes.
- An external-study claim would require a *new, pre-outcome frozen* source, documented independent calibration/test animal roster, comparable altitude/state and predictor fields, and explicit score-exchangeability argument. **No new biological or methods benchmark is opened in this technical note.**

## References for the statistical context (not claims of novel conformal theory)
- Dunn, R., Wasserman, L. & Ramdas, A. (2023). *Distribution-Free Prediction Sets for Two-Layer Hierarchical Models*. Journal of the American Statistical Association 118, 2491–2502. https://doi.org/10.1080/01621459.2022.2060112

- Angelopoulos, A. N. & Bates, S. (2023). *Conformal Prediction: A Gentle Introduction*. Foundations and Trends in Machine Learning. https://doi.org/10.1561/2200000101
- Tibshirani, R. J., Barber, R. F., Candès, E. J. & Ramdas, A. (2019). *Conformal Prediction Under Covariate Shift*. NeurIPS 32. https://proceedings.neurips.cc/paper_files/paper/2019/hash/8fb21ee7a2207526da55a679f0332de2-Abstract.html
- Barber, R. F., Candès, E. J., Ramdas, A. & Tibshirani, R. J. (2023). *Conformal prediction beyond exchangeability*. Annals of Statistics 51, 816–845. https://doi.org/10.1214/23-AOS2276
- Gibbs, I., Cherian, J. J. & Candès, E. J. (2025). *Conformal prediction with conditional guarantees*. Journal of the Royal Statistical Society: Series B 87, 1100–1126. https://doi.org/10.1093/jrsssb/qkaf008
