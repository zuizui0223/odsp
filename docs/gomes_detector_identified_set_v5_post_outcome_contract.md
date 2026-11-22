# Gomes detector-uncertainty partial-identification diagnostic v5 (post-original-count, 2026-11-22)

## Status and rationale

**This is a transparently post-outcome descriptive sensitivity analysis.** The Gomes v4 original `Number` counts were already opened and produced observed `I(Bat;recorded POS|HOUR)=0.1761303797` nats, +0.1136058223 nats/count heldout 8/9 days and a 95% descriptive day-bootstrap interval spanning zero. The v4 conclusion stays `mixed_days`. This new analysis does **not** constitute an independently preregistered hypothesis test, a calibrated detection correction, or another replicated original dataset. No source subset, cutoff or Gamma range may be selected in response to v5 outcomes for confirmatory promotion.

The objective is to turn the earlier single plug-in threshold `Gamma_min=78.1345` into an inspectable **conditional identified-set curve**: for an explicitly stipulated maximum detector probability ratio, how much pairwise high/low detector-stratum separation **must** remain in a hypothetical latent acoustic-event intensity world consistent with the *estimated* observed count table?

## Mathematical target

For each acoustic label s and recorded layer z∈{above,below}, suppose the expected detected rate is `y_sz = q_sz * lambda_sz`, where `lambda` is a hypothetical true call-availability intensity and `q_sz∈[1/Gamma,1]`, with **equal source-level effort normalization** for the two strata (not established beyond published instrument programming). The `q` may freely differ across label and stratum but is fixed for this *pooled* illustrative table. For strictly positive `y`, latent above odds `r_s` must lie in `[o_s/Gamma, Gamma*o_s]`, where `o_s=y_s,above/y_s,below`.

Equivalently the latent above fraction `p_s` lies in
`[y_hi/(y_hi+Gamma*y_lo), Gamma*y_hi/(Gamma*y_hi+y_lo)]`.

For a pair of acoustic labels (s,t) in a single notional source cell, the exact minimum unavoidable `|p_s-p_t|` over all admissible detector q is the distance between these intervals:
`d_min(s,t)=max(0, lower_s-upper_t,lower_t-upper_s)`.
This is also the minimum inflation of a **single-cell two-stratum Schoener overlap** due to collapsing height, because horizontal overlap is trivially one and stratified overlap is `1-|p_s-p_t|`. It does **not** equal field geographic overlap inflation; no physical study-site IDs are present.

The global condition for **all labels to share an identical latent above probability** is `Gamma >= sqrt(max_s o_s/min_s o_s)`. At equality, the intervals share a point. The magnitude of q needed to make the point estimate compatible with *zero* latent community label×stratum information is `Gamma_min`, conditional on this simple observation model, not a measured field q ratio.

**Conservative analytical lower bound on the latent binary-layer mutual information**: let `w_s=y_s,above+y_s,below` and `Y=sum_s w_s`. The unknown latent label share is bounded below by `pi_s>=w_s/(Gamma*Y)`. By Pinsker's inequality `KL(Ber(p)||Ber(p_bar))>=2*(p-p_bar)^2` (natural logs),
`I(S;Z)>=2/(Gamma^2 * Y^2) * sum_{s<t} w_s*w_t*d_min(s,t)^2`.
This bound is deliberately loose and is valid for strictly positive **expected** `y`; using finite observed counts plus Jeffreys smoothing is a *plug-in numerical demonstration*, not a sampling-robust credible/confidence lower bound.

## Fixed descriptive calculations

- Retain the **same 17 acoustic classes** selected in Gomes v4 by the original author's published R rule `sum(Number)>5`; also show all-21-label `Gamma_min` only for comparison.
- For each retained class and above/below, sum original `Number` across all 9 DAYs. Preserve zeros and use **0.5 Jeffreys** in each class/layer cell solely for the plug-in interval/odds calculations, matching the v4 original diagnostic.
- Evaluate the following **illustrative, not empirically asserted** Gamma upper bounds: `[1,2,5,10,20,50,100]`. Each Gamma scenario uses the same classes, same counts, the same `y+0.5` support and same formula. For each report the number of class-pairs with strictly positive unavoidable separation, maximum pairwise `d_min`, pair-average lower bound and source-mass Pinsker-derived conservative `I_min`. This is NOT new day-level predictive validation.
- Recompute `Gamma_min` from the same source to require numerical identity (within 1e-10) with previously archived v4 `78.13449942247023` for retained classes, otherwise STOP as a denominator mismatch.
- Whole-DAY bootstrap `B=5000` with declared seed `20261122`, resampling the 9 entire DAY tables (not individual passes). Keep original v4 17-class roster fixed; compute plug-in `Gamma_min` for each resampled 9-day pool with the same 0.5 smoothing. Report percentile 2.5/50/97.5% as **descriptive source-night instability**; it does not calibrate detector q or prove the original-year population parameter. We have 9 nights from one source and cannot infer independent study sites.
- No species-level ecological label claims, no sonotype-to-taxon assignments, no height in meters, no tuning after these results, no causal moonlight explanation.

## Caveats before real input

The underlying expected-rate relation `y=q*lambda` assumes one detector-specific registration rate per class×stratum and equal relevant effort, whereas actual bat behavior/echolocation and multiple calls per individual violate simple Poisson independence. `Gamma` bounds refer to probabilities, **not** 8–30 m geometric detection radii, which cannot be converted to ratios without source distribution/beam/volume assumptions. The 0.5 prior means even cells with zero recorded events are treated as positive for finite-count plug-in; this is NOT a statement of measured positive expected counts. If detection differs across DAY/HOUR or instrument/position, a single pooled `q_sz` is inadequate and the identified-set exercise should be read only as a restrictive illustrative model.

The field result remains observed-level transferable `mixed_days`, not verified 3D species distributions. Original N2 and JAE packages remain protected.
