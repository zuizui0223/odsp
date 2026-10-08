# TERMINAL HOLD — Camera dates are retrospectively image-corrected

**This correction supersedes any claim below that published Start_Date and
End_Date provide detection-outcome-independent physical installation dates.**
Rooney et al. (2026), PDF p. 8/28, Section 2.4, explicitly report that
the authors modified the deployment start/end dates in R to match the first
and last photographs in the sequence file. The Dryad variable dictionary
describes their nominal field meanings but does not undo that cleaning step.

Therefore the separately frozen calendar-v1 screen is **NOT a valid
pre-response site-selection design**. It is terminally classified
`TERMINAL_HOLD_SOURCE_DATE_COLUMNS_ARE_IMAGE_DERIVED` in
`ODSP_SNAPSHOT_USA_2024_CALENDAR_V1_SOURCE_SEMANTICS_STOP.json`.
The current branch workflow has been rewritten to produce a metadata-free
STOP receipt rather than make any NEW deployment download request. Older
already-queued workflow executions may have a frozen prior commit and
cannot be retrospectively canceled with the available connector; if they
run, the numbers are purely retrospective source structure and **cannot
rescue v1**. This is a publication-methods finding made after the v1 design
freeze, not a v1 empirical qualification outcome.

The independent testing-theory result in the second half of this document
does not depend on the published date-field semantics and remains valid
as a conditional mathematical argument. But no real Snapshot USA
prediction power or future-refit ecological probability has been measured.

Authoritative public method source:
https://doi.org/10.1111/geb.70229 (PDF page 8 of 28, data cleaning).

---

# Snapshot USA 2024: calendar-placement screen v1 and a general statistical no-go bound

**Status: separate outcome-free structural DESIGN, not ecological results or a
qualified ODSP inferential route.** This v1 is stacked on PR #218, but never
changes its v0 source selection, first metadata receipt, or frozen statistical
calibration. Its own contract was frozen at commit 4cff300f BEFORE the first
v1 calendar-metadata scan. Public source summaries and the old v0 source
screen were known; complete global historical metadata non-access is not
claimed.

## The source-semantics correction is a new estimand

Rooney et al. 2026 (DOI 10.1111/geb.70229) describe Survey_Nights as
derived from the first and last IMAGE timestamp per deployment. So the v0
site filter (Survey_Nights >= 30) is acceptable only for retrospective
deployment structural description, not proof of outcome-independent
preassignment.

The Dryad README for DOI 10.5061/dryad.bnzs7h4qf describes Start_Date
and End_Date as the dates of camera physical placement and retrieval.
V1 **never reads the Survey_Nights column** (though it may be present in
the deployment CSV). A v1 site's count qualification instead needs at
least one single physical placement-to-retrieval interval with >= 30
calendar nights. No potentially overlapping intervals are summed.

This identifies *calendar-span candidates*, not devices known to be
operating for 30 nights. Actual uptime and local-time detection effort
remain unknown. A site may be installed but malfunctioning; a
camera's recorded first/last images can also reflect animal movement.

The same prespecified forest/grassland Habitat groups, one physical site
per (Project, Array, Site) composite, at least eight sites and eight
arrays per group, and optional non-replacing feature filter remain as
NEW V1 restrictions (not retroactive edits to V0).

All conflicting repeated deployment IDs crossing sites, site geographies,
site habitat, unparseable dates and other disqualifying metadata are
handled conservatively. No site coordinates or IDs go in the output.

No new sequence record, animal species, observation time or camera
detection file is retrieved by the v1 runner. A failed download produces
SOURCE_METADATA_UNAVAILABLE_OR_INVALID and no file substitution.

## Structural count is not the ecological sample size

Site and camera array counts from this survey are not iid block counts.
Arrays were contributor-run and vary in design. Individual cameras
within an array can share habitat, observer decisions and weather;
this may require treating the entire array as a dependent cluster.
A photo count or camera-night count cannot create independent spatial
replication.

The older ODSP Snapshot Serengeti validation is a different source,
with a frozen terminal result. No earlier observed data or terminal
category is reopened by this v1.

## A stronger general no-go theorem for weak bounded gains

The previous PR #218 calculated a power upper bound for ONE SPECIFIC
e-value betting mixture, using its alternative expectation.

The additional module
odsp/weak_gain_nonparametric_barrier_v1.py
shows that even changing statistical tests cannot necessarily solve
the independent-block limitation. This new result concerns ANY level-a
test valid against the full nonparametric one-sided iid-block null,
where every block-level gain lies in [L,U] and has mean <= tau.

Consider the maximally regular positive alternative:

    P1(X = d) = 1, for d > tau.

Build a legitimate boundary null using only d and the lower support L:

    P0(X = d) = (tau-L)/(d-L) = p0,
    P0(X = L) = 1-p0.

Then E0[X]=tau, so P0 is IN the null. But under this null the complete
all-positive sample (d,...,d) occurs with probability p0^B.

If phi is any level-a test (including randomized tests), its rejection
probability on the all-positive sample obeys

    phi(d,...,d) <= min(1, a / p0^B).

This is its power under the point alternative P1, since P1 always
produces that sample. For NONRANDOMIZED tests, phi is 0 or 1; hence if
p0^B > a, the test CANNOT reject the all-positive sample at all.
Therefore, its power is identically ZERO at P1.

The minimum B that *permits* a nonrandomized distribution-free
test to reject this point sample is

    B_min = ceil(log(a) / log(p0)).

The quantity is a necessary threshold for that point alternative, not
a guarantee that realistic noisy samples will pass. The proof does
not depend on normality, variance estimation, clustering correction or
the original e-IUT method.

### Implication under the experimental alpha=0.002, L=-1, tau=0

| Point alternative block gain d | B_min for any nonrandomized level-a rejection |
|---:|---:|
| +0.02 | 314 |
| +0.05 | 128 |
| +0.10 | 66 |
| +0.20 | 35 |

Under the public 184-array, rounded 77%-forest report,
at most 43 arrays could be nonforest and grassland is a subset.
If all 43 grassland arrays could be treated as iid blocks (which
remains UNVERIFIED), the d=+0.05 point alternative gives

    p0 = 1/1.05,
    P0(all 43 equal +0.05) = (1/1.05)^43 ≈ 0.1227044,
    alpha/P0(event) ≈ 0.0162993.

Thus ANY valid randomized distribution-free test has power <=1.63%
at that point alternative, and any NONRANDOMIZED test has power ZERO.
This is a *conditional impossibility argument* and is not a claim
that the survey's real mean gain is +0.05. It also does not rule out
powerful methods under additional defensible distribution or
sampling assumptions.

For the original frozen PR #217 e-IUT specifically, the previously
computed alternative-expectation bound for B=43 and mu<=+0.05 is
stricter (<=0.88%), because the test is a particular conservative
e-betting mixture. The general testing barrier instead explains why
there is no general distribution-free fix merely by searching for
a nicer significance test when physical replication is so limited.

This separates two scientific priorities:

1. Whether richer information genuinely predicts new ecological
   states at independent sites (a one-sided held-out predictive
   gain question, already addressed by qualified ODSP mean-gain routes);
2. Whether one independently refitted model will almost surely
   improve EVERY group and information contrast (a much stronger
   process probability question requiring far more information).

Do not equate these estimands. In particular, a strong positive
ecological mean result is not disqualified because a more demanding
future-refit reliability probability cannot be certified.

## Status and next decision gate

The deployment-only calendar workflow may produce actual structural
site/array counts once GitHub Actions processes its queue. Whatever
they are, v1 will report only candidate site counts, and must not
register an external ODSP model-to-score endpoint.

Given the general testing barrier, an actual small normalized Brier
gain and scarce independent sites would justify **stopping** the
p_success>0.8 route for this particular ecological validation design,
not reoptimizing alpha, habitat groups or a test after outcomes.

The best science-first continuation is to use an independent,
properly frozen ecological site-based transfer question with an
interpretable block sampling design, rather than treat stochastic
future-model certification as a prerequisite for every N2 result.
