# BOP / Dryad external roster capacity: aggregate bounds and design power v1

Status: **source-free post-metadata exploratory audit; external empirical
admission remains HOLD.** This is a new calculation from already published
aggregate counts, not an estimate of predictive skill or a prospective
biological outcome test. The count and power observations preceded this
implementation. No GPS, identities, target labels or provider sidecars were
downloaded for this route.

## Count result

Dryad DOI 10.5061/dryad.n8pk0p398 documents 280 animals, of which 271
appear in Data_1a (raw GPS MSL height, unlike corrected flight-only Data_2a).
The frozen metadata contract and two BOP reference rosters (v3: 35,
v2026: 45 distinct source IDs) supply the aggregate counts. Both source
versions are included, not only the original 30 scored birds, to avoid
underestimating potential overlap with any previously seen BOP animal.

Let N_s be the Dryad whole-source count of species s, T_s the number
of source IDs of that species in an excluded BOP reference roster, and D=9
the shared budget of animals missing from Data_1a. Conditional on accurate
distinct biological target counts, stable taxon assignment, the retained
sample being a subset of the reported source, and the reference-ID counts
being upper bounds on previously exposed real animals, a sharp marginal
lower bound is max(0,N_s - T_s - D). The upper bound is min(N_s,271)
when no cross-provider overlap is known to be forced. The lower bound
allows all omitted animals and all possible overlapping animals to be
distinct and concentrated in the selected species. It does not identify
which animals remain. The bounds concern Data_1a membership before further
feature availability, quality, cohort selection and outcome eligibility.

| Species | Whole source | BOP v3 | v3 lower | BOP v2026 | v2026 lower |
|---|---:|---:|---:|---:|---:|
| Circus pygargus | 101 | 9 | 83 | 10 | 82 |
| Circus cyaneus | 54 | 9 | 36 | 9 | 36 |
| Circus aeruginosus | 31 | 9 | 13 | 15 | 7 |
| Buteo buteo | 31 | 5 | 17 | 6 | 16 |

For the four species jointly, subtract the nine missing animals once,
not four times: the lower bounds are 176 (v3) and 168 (v2026), with upper
bound 217. Individual marginal minima need not occur simultaneously.
These joint totals CANNOT be pooled to satisfy a within-species content test.

For the #303 default design (29 calibration + one reserved validation),
C. pygargus and C. cyaneus have enough raw count capacity even under
worst-case overlap; their additional attrition budgets under the more
conservative v2026 exclusion are 52 and 6 respectively. The other two
species are neither impossible nor guaranteed by these margins alone.
No raw source eligibility or cross-provider nonoverlap is verified.

## Power is distinct from count feasibility

For fixed calibration n, let k be the largest nonpositive count for which
P[Binomial(n,.1)<=k] <= .05. For a hypothetical IID positive fraction p,
power is P[Binomial(n,1-p)<=k]. The exact rational calculation gives
power .225936 at n=29 if p=.95. The test is discrete and power need not
increase at every successive n. We enumerate every *fixed* n up to the
optimistic whole-source upper bound minus one reserved individual.
For C. pygargus, even the best fixed design with n<=100 has power only
.539429 at p=.95 (n=89, k=4). At p=.98 the optimistic ceiling is
.966598 (n=89, k=4). These are hypothetical design alternatives,
not estimates of biological success rates; actual eligible n may be smaller.
They do not authorize outcome-driven sample-size selection or pooling.

## Additional observation-process blocker

The accompanying Schaub et al. article, DOI 10.1002/2688-8319.70315,
sections 2.1–2.2, analyzes breeding birds in specified study areas and
restricts its analyses to daylight; four BOP taxa use a -6 degree solar
elevation cutoff. Tracking schedules differ between day and night.
It is not yet verified how much of that restriction is already applied
to the actual distributed Data_1a rows. The existing reduced model's
binary 06–18 mean-solar-clock context is not an astronomical daylight
indicator. Do not assume the target has comparable support in both bins,
all-year migration coverage, a common event opportunity process, or
unbiased biological time use. Before selecting any real source endpoint,
inspect documented selection and time/longitude features separately from
altitude labels, establish common observation semantics and a new frozen
model if necessary. The successful-breeding-season sidecar is explicitly
outcome-selected and is not a complete identity roster.

The earlier authoritative Dryad replay (BOP_DRYAD_FIRST_ARTIFACT_RECHECK_V3_RECEIPT.json)
records HTTP 403 for all three small file requests. We did not retry or
substitute a mirror. An openly licensed publication is not a successful
file download. Needed next input is a provider-authorized, version-pinned
all-animal Data_1a identity roster plus its mapping to the BOP reference IDs
(or authoritative evidence of biological nonoverlap), with an independent
sampling-design justification. No candidate is admitted by the arithmetic.

Sources:
- https://doi.org/10.5061/dryad.n8pk0p398 (official README and counts)
- https://doi.org/10.1002/2688-8319.70315 (observation and analysis scope)
- research/BOP_DRYAD_EXTERNAL_SCHEMA_PREFLIGHT_V1_CONTRACT.json
- research/BOP_V3_V2026_REFERENCE_ONLY_GATE_V1_FIRST_RESULT.json
- BOP_DRYAD_FIRST_ARTIFACT_RECHECK_V3_RECEIPT.json

Reproduce offline:
~~~bash
python scripts/audit_bop_dryad_roster_capacity_v1.py
python -m pytest -q tests/test_bop_dryad_roster_capacity_v1.py
~~~

The script checks pinned Git blob SHA1s before parsing, uses only the
three existing aggregate source records and emits aggregate bounds and
exact-binomial design calculations. The tests enumerate every retained
subset and possible overlap in small finite universes to verify sharp
bounds, and compare exact probability boundaries with combinatorial
sums. Neither legacy receipts nor the original RF/content/rank code
is changed.
