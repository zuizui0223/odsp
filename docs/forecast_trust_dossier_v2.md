# Forecast trust dossier v2

`odsp.forecast_trust_dossier_v2` composes the latest ODSP trust evidence into one explicit decision trace without inventing a scalar confidence score.

## Evidence layers

The dossier keeps five layers separate:

1. **Validation** — independent-group point transfer, group-wise empirical coverage, and joint block-bootstrap x bounded-reweighting robustness.
2. **Robustness profile** — caller-supplied sampling-weight scenarios plus a deterministic bounded-reweighting stress test and critical gamma.
3. **Deployment** — environmental novelty and strict extrapolation on new prediction rows.
4. **Selection** — bias-robust trusted status, Pareto membership, and recommendation.
5. **Decision trace** — a readable sequence of the above statuses, blockers, and warnings.

Validation admission is inherited from `BiasRobustCandidateScore.bias_robust_trusted_admissible`. Later sensitivity or deployment diagnostics do not rewrite that history. They are added as warnings.

## Example interpretation

A dossier may say:

- validation: admitted at gamma 1.5;
- sampling-weight audit: not audited;
- bounded-reweighting stress: gamma-sensitive at gamma 2.0;
- minimum finite critical gamma: about 1.73;
- deployment: in-domain;
- selection: not compared.

This means the candidate passed its declared validation stress but a stronger, separately declared reweighting envelope can overturn the sign. It does **not** mean gamma is an estimated probability of bias or that 1.73 is a biological threshold.

Another dossier may remain validation-admitted while the deployment section reports `strict_extrapolation_warning`. Extrapolation is a deployment warning; it does not retroactively change the validation result.

## Claim boundary

The dossier is presentation and decision-traceability infrastructure over existing evidence. It does not add statistical evidence, infer a correct sampling process, prove absence of observation bias, turn environmental novelty into an error probability, or guarantee performance under future distribution shift.
