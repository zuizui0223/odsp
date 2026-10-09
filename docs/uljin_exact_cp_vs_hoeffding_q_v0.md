# Same 5% ecological certification guarantee with fewer independent camera references?

**Source-free post-PR248 design comparison, not a real ungulate result.**
PR248 used four simultaneous Hoeffding detector q bands to bound
season×solar-phase detector efficiency, then exact one-sided Fisher
animal detected-count testing with split budgets alpha_cal=.025 and
alpha_animal=.025. The first simulated positive-world result was
81.5% certification at n=1000 true passage references PER bin, but
Hoeffding bands are conservative and could waste field sensor effort.

A distinct post-parent freeze now asks whether **EXACT two-sided
Clopper–Pearson (CP) binomial confidence intervals with Bonferroni**
can obtain tighter q bounds for the SAME target and alpha.

For each of the FOUR independently referenced q values, choose a
two-sided CP interval with marginal noncoverage <=.025/4=.00625,
therefore allocate .003125 to each one-sided binomial tail. If S
detections out of n independently verified true opportunities, the
lower endpoint solves

    P_q(Bin(n,q)>=S)=.003125  (S>0; otherwise lower=0),

and the upper endpoint solves

    P_q(Bin(n,q)<=S)=.003125  (S<n; otherwise upper=1).

Union bound over four intervals guarantees all four true camera
detector sensitivities are covered with probability >=.975.
For a binomial calibration separately independent of the animal
Poisson process and its source site/date eligibility, combining
this calibration with Fisher exact at alpha_test=.025 maintains
the same <=.05 overall false-certification bound. The exact CP
coverage is usually conservative, NOT guaranteed equal to .975.

For the same four q cells, detector seasonal crossproduct upper
limit is B=q_fall_early_upper*q_rise_late_upper /
(q_rise_early_lower*q_fall_late_lower). B is infinite and the
ecological inference is HOLD if a denominator lower bound reaches
zero. Exactly the same parent count table, independently logged
effort OR and exact noncentral Fisher right tail at theta_effort*B
are used. The underlying biological assumption that q transfers
from reference-trigger opportunities to real species movements is
still unverified.

## Frozen evaluation — honest post-parent design

The first PR248 Hoeffding outcomes are already known and disclosed.
This is a NEW prospectively frozen **deterministic comparison of
representative independent calibration COUNT OUTCOMES**, not a
blinded evaluation or Monte Carlo detection power simulation.
For q=(q1,q2,q3,q4) under each of four previously frozen artificial
worlds, the observed reference count in each cell is round(n*q),
with n=50,200,1000,5000 only. For all 4×4=16 paired instances,
compute CP and Hoeffding B, exact animal robust one-sided p,
animal OR lower bound, whether the source-free original fixed
observed count would be certified, and the first passing n level
on the frozen grid for the strong artificial encounter scenario.
This identifies a possible **information-efficiency improvement
under representative calibration outcomes** but DOES NOT show
mean required sample size, coverage in the wild, cost savings or
new statistical power.

The CP binomial tails are inverted through frozen-order stable
log-binomial-coefficient normalization and 52 bisection iterations
with explicit numerical accuracy tests. No scipy or new dependency,
no animal/source ZIP, no detector sensor observations, and no
rationalization of first PR248 results after exposure.

Real ecological field admission still requires species-specific
reference sensors and correct opportunity labels, independent
source-original camera uptime, q variation with vegetation and
weather, original frozen station/day/taxon roster, geographic
solar-time uncertainty, and adequate detection support. A
successful season-specific phase predictor alone does not prove
latent animal circadian change or an endogenous photoperiod clock.
