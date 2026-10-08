# Design feasibility after the frozen v1/v2 future-refit probability failures

**Status:** post-qualification planning analysis only. This is not an
alternative qualification receipt, a reinterpreted v2 pass, or a modification
of the frozen v1/v2 generators or inferential algorithms.

## What probability question should the experiment answer?

Let (p_{\mathrm{success}}\) denote the chance that *one future, iid refit*
from the declared and frozen training process passes **every** required
validation-population directional-gain cell. The natural operational decision
is a lower confidence-bound threshold:

> Is the evidence strong enough to certify (p_{\mathrm{success}}>q\)
> for a scientifically predeclared target (q\), such as 0.8 or 0.9?

This is different from the diagnostic event (K=R\), in which **all**
observed refits are certified. At some sample sizes (K<R\) can still
yield (L(K,R)>q\). Therefore a *success-probability decision* should
eventually be evaluated by the probability of
(L_{\mathrm{CP}}(K,R)>q\), not exclusively by (P(K=R)\).

The current v1 and v2 were explicitly qualified against
(P(K=R)\ge0.8\), and both **failed** their own frozen gates.
This suggested alternative decision metric cannot retroactively rescue them.

## Exact binomial information ceiling

With the process-stage error budget held at
(\alpha_p=0.025\), the exact one-sided Clopper–Pearson lower bound
has maximum

\[
L_{\mathrm{CP}}(R,R)=\alpha_p^{1/R}.
\]

Even perfect validation certification of every refit cannot exceed this
ceiling. A necessary condition to certify (p_{\mathrm{success}}>q\)
is

\[
R>\frac{\log(\alpha_p)}{\log(q)}.
\]

Strict inequalities matter. Sample-size and certification-count calculations
using the exact binomial inversion:

| Observed refits R | Validation alpha per refit (0.025/R) | Max possible CP lower bound | Minimum certified K for lower >0.8 | Minimum K for lower >0.9 |
|---:|---:|---:|---:|---:|
| 8 | 0.003125 | 0.631 | impossible | impossible |
| 17 | 0.001471 | 0.805 | 17 | impossible |
| 20 | 0.001250 | 0.832 | 20 | impossible |
| 30 | 0.000833 | 0.884 | 29 | impossible |
| 36 | 0.000694 | 0.903 | 34 | 36 |
| 50 | 0.000500 | 0.929 | 46 | 50 |
| 72 | 0.000347 | 0.950 | 65 | 70 |
| 100 | 0.000250 | 0.964 | 89 | 96 |

For **R=20**, one failed certification already prevents claiming
(p_{\mathrm{success}}>0.8\): the lower bound with (K=19\) is
approximately **0.751**, versus **0.832** with (K=20\).
With (K=17\), it is approximately **0.621**.

Consequently, the frozen v2 R=20, B=8 all-certified power of **0.096**
is not an irrelevant gate: if the scientific target had been (q=0.8\),
it would also imply only 9.6% probability of certifying this target under
its particular strong-signal scenario. But the scientific target **was not**
part of the v2 frozen qualification and cannot be imposed retroactively.

## A tension that prevents 'more refits' from being a free fix

Larger R improves the binomial-information ceiling, but in the frozen
refit-level IUT approach the validation component significance is

\[
\alpha_{v,r}=\frac{0.025}{R}.
\]

Larger R makes **each observed refit harder to certify**, particularly with
small B. This can reduce the achieved K/R enough to counteract the gain from
larger R.

The fixed B=8 worlds expose precisely this tension. At an 8-oracle-SE shift:

- V2 R=8: mean K **7.827** and (P(K=R)=0.852\).
- V2 R=20: mean K **17.03** and (P(K=R)=0.096\).

These are observed simulation summaries for a specific frozen generator,
not general power laws. R and B should be designed together.

## What to preregister for a *distinct* successor

Before any next qualification run, freeze a scientific threshold q, target
probability of making that decision, source/validation dependence assumptions,
R/B design grid, and a maximum resource or runtime budget.

Possible mandatory diagnostics include the distribution of certified counts K,
the distribution of (L_{\mathrm{CP}}(K,R)\), the probability of
(L_{\mathrm{CP}}>q\), probability of false overstatement, and failures caused
by validation-stage non-estimability. A new method must demonstrate
validation-component type-I control under the declared block sampling regime.
All empirical p-success inferences must remain conditional on the same frozen
source and require a separate process-provenance wrapper.

**Do not** retain the v2 method and merely lower the original all-certified
power gate, raise the oracle-effect size after exposure, or discard the
R=20/B=8 case. Such actions would not qualify the frozen v2.
