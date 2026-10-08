# Exact detection-count requirement for one within-site seasonal two-bin contrast

**Status: source-free idealized exact conditional power calculation only.**

Parent PR #241 established that two exact missing 3-way count cells can
resolve an odds ratio given the other previously released *realized*
two-way count margins. That deterministic information-grain claim does
**not** say how many animal detections are needed to estimate the
odds ratio with a calibrated statistical test under sampling uncertainty.

This separate route freezes one physical site/date pair, two
preselected solar-phase bins (early and late), full equal camera uptime,
and non-differential or odds-crossproduct-neutral detection probability.
Suppose the observed 2×2 table has row totals n events for
rising and falling seasons and column totals n for each bin.
Then N=2n is the total events across those two bins in BOTH branches;
it is not n per site across the entire year, nor four times n.

Conditioning on these fixed row/column margins, define X = falling
detections in the EARLY bin. Under independent Poisson cell rates and
true observed odds ratio θ:

    P_θ(X=x | fixed margins) ∝ choose(n,x)^2 θ^x.

The one-sided exact Fisher test of θ≤1 versus θ>1 rejects for
upper tail probability P_1(X≥x)≤0.05, with no mid-p adjustment.
The exact conditional size is ≤5%, not necessarily 5% because
the distribution is discrete. The power at each fixed margin n is
the exact corresponding noncentral hypergeometric rejection tail.

Freeze true ORs 1.0, 1.5, 2.0 and 3.0, predeclared n grid
10/20/40/80/160/320/640, and scan every integer n=5..640.
Report first n achieving ≥80% conditional power and also the
smallest n whose power stays ≥80% at EVERY larger n up to 640,
because exact discreteness can make raw power vs n nonmonotonic.
Do not relax this target or search additional effects after outcome.

**These sample sizes cannot be directly applied to the 2022 Uljin
camera-trap observations:** published 4,623 independent detections are
across four taxa and an entire year, not two bins of one selected
physical site's mirrored photoperiod dates. Real hour-level source
uptime and local timestamps remain unauthenticated. A season×bin
crossproduct in recording effort or detection probability can mimic
the activity odds ratio even when all detection counts and operating
hours are accurately observed. Also this 2-bin fixed contrast is not
a 6-bin global interaction test, and searching among bins/taxa/sites
would require a new multiple-testing plan. Clustering, heterogeneity,
animal presence and site-level power/precision are outside this toy
calculation.

Thus this is an **exact, inspectable design sensitivity benchmark**,
not an empirical power or minimum full-study sample size, new
biological discovery, or new general theory. Qualified ODSP prior
routes remain unchanged.
