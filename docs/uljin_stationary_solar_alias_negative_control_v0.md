# Source-free geometric counterexample: clock time is not solar phase

**Status:** synthetic/oracle methodological falsification only; separate stacked
draft route. This does not inspect any Uljin ungulate events, camera-station
operation histories or precise locations. The original 41 astronomical mirror
pairs and any previous ODSP primary evidence remain unchanged.

## Scientific question

Even at precisely matched daylength, can a positive held-out branch×civil-clock
shape signal occur when the true animal detection intensity is **identical as
a function of solar phase** on both dates? Yes, structurally.

Fix the original May 1 versus Aug 13, 2022 mirror pair. Define a single shared
rate per solar-phase hour, with baseline 1 and a narrow additional hotspot of
1000 per phase hour centered at the solar phase that was 07:56:24 civil time
on the rising date. Use complete 24h uptime on both dates. For each civil-clock
bin C on date d, the expected count is

  mu(d,C) = integral_{t in C} lambda(phi_d(t)) * phi'_d(t) dt.

In solar-phase bin P, the same expected count is

  mu(d,P) = integral_{phi in P} lambda(phi) dphi

for **both** dates. The latter formula requires transforming camera uptime,
not merely shifting event timestamps. The published daylength-mirror criterion
does not align civil solar noon because of the equation of time.

For equal within-bin efforts, the oracle null has a common falling fraction
p0=Sum(mu_D)/Sum(mu_A+mu_D). The oracle six-bin alternative has
pk=mu_D,k/(mu_A,k+mu_D,k). Its expected conditional logscore gain is

  Sum_k [mu_D,k log(pk/p0) + mu_A,k log((1-pk)/(1-p0))].

A positive civil-clock gain under this stationary solar-phase world is a
**counterexample to interpreting clock-bin improvement as biological
photoperiod hysteresis**. The solar-phase gain is identically zero.

## Boundaries

This is not an observed biological result, a test-size/power simulation,
a train/heldout predictive validation, proof of solar-only behavior, or an
empirical seasonal effect. Its hotspot is intentionally concentrated close to
the 08:00 civil boundary to expose aliasing; its intensity and effect magnitude
are synthetic and arbitrary. It proves *possibility*, not prevalence.

The negative control assumes full uptime and a simple phase-based Poisson
intensity. Real application requires independent continuous camera-operation
logs and event clock-time semantics, station-specific solar geometry, and
physical station/region independence. The original EcoBank v1.1 archive remains
unverified. None of the source-process, v5, external or fixed-set ODSP routes
are reclassified.
