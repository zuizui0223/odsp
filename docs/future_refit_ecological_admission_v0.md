# Ecological admission and bounded proper-scoring bridge

**Status:** post-v0 statistical calibration, prospective DESIGN assistance only.
No existing ecological endpoint is reclassified or reopened; first frozen
synthetic panel at 2c8700df and its gate remain unchanged.

## The main obstacle is the independent sampling unit

Three different objects must remain distinct:

- ecological observation rows: camera detections, animal GPS fixes or dives;
- independent validation blocks: genuinely selected camera sites, animals or
  other primary units representing a declared validation-block population;
- independent model refits: separately generated models from the exact
  predeclared training stochastic process, all scored on one held-out V.

A camera-hour is not an independent camera site. An hourly-thinned GPS fix
is not an independent animal. Differently named sites may share weather,
observer or spatial shocks. The new e-IUT requires iid validation blocks
within each validation group for any fixed model and independently generated
training-process refits unrelated to held-out outcomes.

### Structural audit of existing closed ecological endpoints

The deterministic auditor scripts/audit_future_refit_ecological_admission_v0.py
reads only FROZEN PRE-OUTCOME CONTRACTS, plus existence (not content) of
terminal outcome files. It neither reads old numerical outcomes nor
downloads source data nor reruns empirical endpoints.

| Closed lane | Frozen transfer design | Structural limitation |
|---|---|---|
| Snapshot Serengeti | One log-score comparison, 3 held-out site folds | Not two contrasts; iid camera-site sampling and iid training refits unverified |
| BOP_RODENT | One primary log-score comparison, 5 tagged-individual folds | Hourly rows are not independent individuals; no frozen iid refit process |
| Tadarida teniotis | One x-y-conditioned vs marginal log-score comparison; 2 sealed bats | Two sealed independent bats cannot imply eight independent validation blocks |
| Tawaki | One sealed log-score comparison | Frozen site-by-year coverage gate failed; no iid refit process |

Site-fold counts are not iid site-block counts. Five independent validation
folds are not five independently generated process refits. Existing
endpoints retain their original classifications; no post-outcome score
recalibration may be called untouched external evidence.

## A mathematically bounded ecological probability score

The adapter in odsp/future_refit_bounded_brier_adapter_v0.py takes
refit x row x three levels x K-category probability predictions, plus
true integer state labels and stable row/refit IDs.

Three information sets are strictly nested. For a fresh camera-trap
survey with six four-hour detected-time bins, a possible planned chain is:

1. pooled detected-time probability P(T);
2. species-identified P(T|species);
3. species plus predeclared environmental context
   P(T|species,season/habitat/climate).

The third level must use predictors AVAILABLE FOR UNSEEN SITES; merely
memorizing a site label does not transport to a new site. Detection-time
variation can still reflect detection bias, not true activity niches.

For observed category y and probability vector p define

    S(p,y) = 1 - 0.5 * sum_k (p[k] - 1[k=y])**2.

This normalized multiclass Brier skill score is in [0,1] on any
K-category probability simplex; the two consecutive score differences
are in [-1,1] WITHOUT post-outcome clipping. It is a strictly proper
score (a positive affine transform of negative multiclass Brier loss).

The adapter rejects invalid simplex output, missing integer state labels,
duplicate row/refit IDs, and nonnested information axes. It does NOT
attest model-generation provenance, prospectivity or iid sampling.

**Historical log-score gains cannot be converted to Brier gains.**
Both the score scale and the target would change. Recompute both
contrasts only from a newly frozen three-level prediction process.

## Outcome-free physical-unit preflight

The separate preflight module checks both row identities and the actual
sampling units of training and validation. Its minimum structural checks:

- the ENTIRE original source row frame and validation row frame have
  distinct stable IDs within a declared namespace;
- physical sampling-unit IDs are supplied for EVERY source and validation
  row and do not overlap across source and validation, even if event IDs
  differ;
- a physical site or individual is not fragmented across independently
  counted blocks within a validation group;
- at least two declared validation groups, eight positive-weight block IDs
  per group, eight unique model-refit IDs, and exactly three prediction levels.

Its return category is STRUCTURALLY_ADMISSIBLE_UNVERIFIED_SAMPLING.
It **never** returns a primary qualified decision. ID separation does not
prove spatial/temporal independence, source chronology, sampling design or
absence of outcome-driven model selection. All those proof flags are false.

A camera site observed over eight nights is ONE site-level block rather than
eight pseudo-independent samples. Repeated events can be averaged inside
the site block. More rows do not mean more independently sampled sites.

## Prospective ecological endpoint that could meet the route

A genuinely NEW validation dataset, whose outcomes are not already opened,
would need to freeze BEFORE outcome access:

1. a six-bin categorical detected-time target, two consecutive bounded
   Brier score gains, and two or more validation habitats/populations;
2. a named camera-site sampling population and genuine random/defensibly
   iid sampling of sites within group; repeated site observations nested
   within site blocks; spatially correlated station clusters either
   explicitly accounted for or not asserted independent;
3. full physical-site separation of frozen training source and validation,
   including every source frame row, not just realized refit memberships;
4. independent fitting/refit schedule, fixed model and scoring code,
   managed refit/model-to-score byte identities, three predictions per row;
5. group, block, site ID, site weights, score definition and first-access
   chronology frozen and verifiable before validation labels are read.

Uniform site-block weighting targets performance at a RANDOM VALIDATION SITE.
It is not an event-weighted mean; different site inclusion probabilities
require separate design justification and possibly different inference.

## Feasibility and claim ceiling

The first 11-world frozen synthetic panel yielded:
positive bounded gain +0.05 and 12 blocks/group: 0.0 decision power;
the same gain and 200 blocks/group: 1.0 decision power under a highly regular
synthetic generator. Neither is real ecological field-data power.

A dataset with 30 cameras and hundreds of thousands of events is still
a 30-camera dataset for a camera-site population target. Repeated events
must not substitute for independent sampling units.

Therefore NONE of the four closed ODSP empirical endpoints can be promoted
retrospectively to the new stochastic future-refit reliability claim.
The next credible ecological test needs a prospective new independent
validation sample and bounded three-level probability scores. 


## Public alternative identified, but NOT admitted

A publicly documented source with sufficient *potential* site scale is
Snapshot Safari 2024 Expansion from LILA BC:

https://lila.science/datasets/snapshot-safari-2024-expansion/

The provider reports 15 camera-trap projects, 4,029,374 images and 1,824
unique camera-location IDs, with annotations in COCO Camera Traps format.
This is a source-discovery lead, not an evaluated ecological endpoint.

CRITICAL: the expansion explicitly includes the already-used Snapshot
Serengeti project (SER), so all training-source-overlapping SER cameras
must be excluded at the physical unit level. Public camera IDs across
projects cannot be presumed sample-exchangeable, mutually independent or
geographically representative. Images/camera counts are not iid block
counts. The number of eligible sites per *predeclared validation group*
after exclusions has not been checked.

The COCO Camera Traps format documents an OPTIONAL per-image datetime
field. The fact that metadata are offered does not prove timestamps,
local-time semantics, effort denominators or species annotations are
complete in this release. Since clock time and species are the actual
ODSP response variables, inspecting per-image timestamp values and
category annotations prior to the response freeze WOULD be outcome
access. We have examined only the public provider's summary counts;
that includes aggregate category frequencies, so complete prior
ignorance of public labels must not be claimed.

Relevant method-design research:

- Goldstein et al. (2024), Methods in Ecology and Evolution,
  doi:10.1111/2041-210X.14359, on temporal autocorrelation in camera
  detection studies.
- Combining Disparate Camera-Trap Surveys (2026), Journal of Biogeography,
  doi:10.1111/jbi.70333, on geographic sampling bias and variation in
  camera-trap survey designs.

The screened source is explicitly locked as
DISCOVERY_ONLY_NOT_ADMITTED in
ODSP_FUTURE_REFIT_SNAPSHOT_SAFARI_SOURCE_SCREEN_V0.json.
No raw per-event labels, timestamps or site-level scores were opened
during this source-screen. No iid validation sampling or outcome-free
provenance is established.

Possible next structural stage: freeze a new site's project/ID exclusion
rules, physical site and sampling design, timezone semantics and
exact metadata/score extraction implementation BEFORE inspecting
response-bearing annotation or timestamp values. If that is not possible,
the candidate is a descriptive public-data study, not a qualified
untouched-external future-refit reliability endpoint.
