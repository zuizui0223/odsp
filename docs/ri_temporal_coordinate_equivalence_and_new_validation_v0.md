# Next independent ecological design: the coordinate is not the mechanism

**Status:** synthetic theory and known-truth falsification only, using no
Rhode Island detection records. This companion lives inside the
existing ODSP RI interpretation PR #228, not a new empirical
paper, route qualification or a retroactive rescue of the original
all-season solar superiority hypothesis (which remains NOT SUPPORTED).

## Why an additional theory test is necessary

The same public RI dataset produced these exploratory findings:

- Pooled solar clock-log-score gain was +0.02746 nats in winter,
  -0.03257 nats in summer (against species-only clock histograms).
- When BOTH families were conditioned on season, their parity
  comparison became -0.03866 winter and -0.03818 summer.
- A matched physical-site bootstrap also returned wholly negative
  POST-RESULT exploratory intervals for the conditional solar-minus-
  clock model comparison. This proves no causal calendar clock.
- Original solar-phase histograms were mapped into civil-clock bins
  using the six-by-six stochastic matrix M(site,date), which limits
  the clock-space probabilities they can represent. Direct clock
  histograms lack this restriction even with the same parameter count.

These facts show that the fixed, binned representations differ in
both inductive bias and effective clock-space capacity. A predictor
won a comparison, but no biological mechanism is identified.

The field-specific evidence predates ODSP: Vazquez et al. (2019),
Methods in Ecology and Evolution, DOI 10.1111/2041-210X.13290,
showed that equinoctial and average double-anchoring are NOT
interchangeable, with **average anchoring often preferable** for
recovering real activity distributions. Thus an equinoctial model
losing against clock does not reject all astronomical predictors.

## A coordinate-change identifiability result

Let t be continuous local civil-clock hour on the 24-hour circle,
z a known solar context (date, latitude, longitude), phi_z(t)
the original two-anchor solar phase (sunrise -> 06 and sunset -> 18),
and J_z(t)=d phi_z(t)/dt. The forward Jacobian is piecewise constant:

    J_z(t) = 12/(sunset-sunrise)                 if daylight
           = 12/(24-(sunset-sunrise))           if nighttime.

For a proper solar-phase density g_z(phi), the corresponding
**civil-clock density** is

    f_z(t)=g_z(phi_z(t)) * J_z(t).

Conversely, every strictly positive civil-clock density f_z(t)
defines

    g_z(phi)= f_z(phi_z^-1(phi)) * d phi_z^-1(phi)/d phi.

These two transforms are exact on the circle apart from
measure-zero sunrise/sunset knots. Both preserve probability
mass and give IDENTICAL pointwise civil-clock likelihoods when
one is a reparameterization of the other.

**Therefore an unrestricted season/site/date-CONDITIONAL solar
density and an unrestricted conditional civil-clock density
have the same representable probability laws.** No passive
detection-time likelihood can determine what the animal's
'internal clock' really is solely from changing the coordinate
names. Causal photoperiod entrainment requires additional
biological or experimental assumptions, not arbitrary
coordinate relabeling.

This is a change-of-variables observation, not a claim of new
mathematical discovery.

## What becomes falsifiable: shared INVARIANCE across contexts

A serious transfer experiment can impose distinct, explicit
predictions before inspecting future outcomes:

H_solar: a common species density g(phi) is invariant
across seasonal solar contexts, so its *civil-clock*
distribution necessarily shifts according to phi_z and J_z.

H_clock: a common species density f(t) is invariant in
civil-clock coordinates, so the *solar-phase* distribution
necessarily changes across seasons.

These are distinct, testable RESTRICTIONS on how a learned
density can vary with date. They are not mathematical
properties of the word 'solar' versus 'clock'.

With season-specific unrestricted functions g_z and f_z,
both represent exactly the same conditional activity/detection
density and should not be compared as separate intrinsic
biological mechanisms.

### The predeclared two-world falsification panel

The source-free module
odsp/ri_temporal_coordinate_equivalence_synthetic_v0.py
implements:

1. Exactly normalized, smooth circular von Mises density
   with fixed concentration 2.2 and peak phase/hour 7.5.
2. Two fixed RI-like solstice contexts: 2022-12-21 and
   2022-06-21 at 41.5°N, 71.5°W.
3. Original astronomical sunrise/sunset with the EXACT
   continuous-phase forward Jacobian and inverse Jacobian.
4. Ideal population-optimal SHARED clock comparator
   under genuine solar-phase invariance:
   the 50/50 mixture of the two true clock densities.
5. Ideal population-optimal SHARED solar comparator under
   genuine civil-clock invariance:
   the 50/50 mixture of the two clock densities transformed
   into phase space with the inverse Jacobian.
6. Strictly proper expected continuous-clock log-density
   scores evaluated over a fixed 24,000-midpoint quadrature
   grid. The true invariant representation should beat
   the best alternate invariant model in its own
   known-truth world, with no finite-bin matrix capacity cap.
7. Independent pointwise forward/inverse consistency tests:
   unrestricted context-dependent solar and civil-clock
   models must give equal civil-clock densities.
8. Explicit DETECTION EFFORT ALIASING counterexample:
   for any positive observed detection density d(t) and
   any strictly positive competing activity density a(t),
   choosing e(t) proportional to d(t)/a(t), scaled to
   lie in [0,1], produces exactly the same normalized
   detected-time distribution.

The last construction means that **even a successful
solar-phase-vs-clock transport comparison is about CAMERA
DETECTIONS** unless camera availability and detectability
are independently measured or successfully modeled.

All scenarios, year/date labels, concentration, quadrature,
support and qualitative gates are frozen in
RI_TEMPORAL_COORDINATE_EQUIVALENCE_SYNTHETIC_V0_CONTRACT.json.
The associated CI reads no public wildlife outcome file.

## Practical forward experimental design

A future independent project should compare transport under
the **same continuous civil-clock log-density target**,
including the change-of-variables Jacobian. Use:

- original, independently logged hardware operating periods
  and clock/DST calibration for all validation sites;
- a documented site sampling design, entire-physical-site
  source/validation exclusion and a frozen external roster;
- a clock-invariant vs solar-phase-invariant prediction, each
  with common species-level density across new dates;
- a distinct season-aware/context-aware flexible control
  that cannot be misread as 'proof of an internal clock';
- training-only selection of smoothing, regularization,
  complexity penalties and phase-anchor functions;
- climate/light/temperature or direct behavioural measurements
  when claiming environmental mechanism, not post-result
  reweighting of photographic detection timestamps.

The relevant ecological outcomes are **which cross-context
invariance predicts new sites and seasons**, and which residual
species-specific seasonal structure remains after controlling
for the date's physical sun geometry. More separate
summaries from the same Rhode Island camera survey cannot
supply independent confirmation.

## Citation context

- Vazquez, Rowcliffe, Spoelstra & Jansen 2019.
  Comparing diel activity patterns of wildlife across latitudes
  and seasons: Time transformations using day length.
  https://doi.org/10.1111/2041-210X.13290
- Rowcliffe et al. 2014. Quantifying levels of animal
  activity using camera trap data.
  https://doi.org/10.1111/2041-210X.12278

Neither paper establishes that ODSP's current Rhode Island
exploratory model signs identify a biological internal clock.
The source cohort is not an iid sample of all mammal
habitats, and the current original result remains
EXPLORATORY_NOT_SUPPORTED_OR_UNAVAILABLE.
