# Future-refit success probability: refit-level IUT v2 (experimental)

## Distinct target

Let (r\sim\mathcal P_{\mathrm{train}}) denote one iid refit from the
**predeclared** process conditional on the frozen empirical training source.
For each independent validation group (g) and ordered information step (c),
let (\theta_{rgc}\) be the expected held-out gain on the specified validation
population. With frozen nonnegative tolerance (\delta),

\[
p_{\mathrm{success}}
 = \Pr_{r\sim\mathcal P_{\mathrm{train}}}\bigl(
       \theta_{rgc}>\delta\;\text{for every required }(g,c)
   \bigr).
\]

This is neither the process-mean target of qualified v5 nor the fixed-set
intersection claim. It does not quantify the chance that a newly sampled
**original ecological training dataset** succeeds.

## Why v1 failed

The prospective v1 used one simultaneous max-t family containing all
(R\times G\times C\) validation cells and then required every cell in a
refit to pass. The frozen v1 run found zero all-refit certification power in
both strong-effect worlds, even though the overclaim gate passed. A separate
**post-failure**, exploratory check of 20 draws in each B=8 world found
median finite max-t critical values 12.73 at R=8 and 19.91 at R=20; no
infinite critical values were observed.

The v1 power failure remains permanently frozen. These diagnostic numbers
cannot be used to change v1's method, seed, significance level or gate.

## Refit-level intersection-union test

For each observed refit (r\), its null is the **union**:

\[
H_{0,r}:\quad\exists(g,c)\text{ such that }\theta_{rgc}\le\delta.
\]

Its alternative is the **intersection** of positive components.
If each component one-sided test has conditional false-rejection probability
at most (a=\alpha_v/R\), then the IUT test for an unsuccessful refit also has
false-rejection probability at most (a\), because at least one component null
must hold:

\[
\Pr(\widehat S_r=1\mid\text{refit }r\text{ unsuccessful})
\le a.
\]

No Bonferroni correction across groups and contrasts is required for this
*AND* claim; the test does **not** support a post-hoc discovery claim for any
particular component. The union bound across the R observed refits gives

\[
\Pr(\exists\text{ falsely certified refit})\le
R(\alpha_v/R)=\alpha_v.
\]

This argument does not require independence across the component tests or
across the observed-refit certification decisions. Shared validation blocks
are therefore retained. Component-size validity is still required, which is
why the chosen block t tests need their own calibration panel.

## Exact process stage

Let (S\) be the number of *truly* successful refits among R iid process
draws and (K\) the number certified by the validation-stage IUT. Then

\[
S\sim\operatorname{Binomial}(R,p_{\mathrm{success}}).
\]

On the no-false-certification event, (K\le S\). Because the one-sided
Clopper–Pearson lower bound (L_{\alpha_p}(k,R)\) is nondecreasing in k,

\[
\Pr\{L_{\alpha_p}(K,R)>p_{\mathrm{success}}\}
\le \alpha_v+\alpha_p.
\]

V2 freezes (\alpha_v=\alpha_p=0.025\), giving a nominal overall
one-sided overstatement budget 0.05, **provided** the validation component
tests have the assumed type-I error control. It does not assume that
validation and training errors are independent.

## V2 numerical candidate

Each group uses declared positive-weight validation blocks as the sampling
units. For each refit and ordered contrast, compute a weighted ratio-of-sums
gain, the one-way cluster plug-in SE, and a one-sided t lower limit at
(1-0.025/R\) with (B_g-1\) degrees of freedom.

A refit is successful only when all limits for all groups and both contrasts
exceed the tolerance. Zero or nonfinite studentizers, missing support or
nonfinite scores fail closed. V2 does **not** resample training refits during
validation inference and does not compute a global max-t pivot.

The Student-t approximation is not exact for arbitrary weighted,
heteroskedastic or heavy-tailed validation blocks. The algebra above is not
a substitute for testing these operating characteristics. No primary status
is allowed before qualification and provenance.

## Prospective gate

The separate v2 contract was committed before seeing any v2 calibration
result. It retains the same six known-p coverage worlds and two strong p=1
power worlds as the v1 panel, with the same split alpha and unchanged
thresholds. First run seed 20261019; 1,000 simulations per scenario.

If the 8-SE p=1, B=8 power gate fails, this **v2 is a recorded failure**.
Neither B, alpha, R, the shift nor the required 0.80 power threshold may be
changed afterward to rescue the result.

## Practical implication

Even an ideal validation classifier cannot overcome the exact binomial
sample-size ceiling: if all R observed refits are certified,

\[
L_{0.025}(R,R)=0.025^{1/R}.
\]

For R=8 this is approximately 0.631; R=20 approximately 0.832. Thus
a claim that the next process refit succeeds with probability greater
than 0.9 is not obtainable from only 20 observed refits, regardless of
how strong their gains look.
