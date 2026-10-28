# Western marsh harriers: external **reference-only** source screen (v1 → v2)

## Reason for this screen

ODSP's frozen BOP_RODENT bird-state model had 27/30 positive
individual-level log-score gains but an overall **mixed** terminal.
The independent new-animal gain method requires, per species, at least
nine unshared calibration individuals and one untouched future test
individual to obtain a nonvacuous 90% rank lower limit. Thousands of
GPS fixes or different tracking-device IDs do not substitute for those
biological units.

Two separate published datasets of western marsh harriers
*Circus aeruginosus* appear potentially useful but must pass **source
identity and cluster** checks before any GPS response data may open:

- **MH_WATERLAND**, INBO/LifeWatch UvA-BiTS (Movebank study 604806671),
  pinned Zenodo v7 DOI 10.5281/zenodo.10053583, published total
  **seven animals**, source reference CSV MD5
  \`b76cc93d9be67b814f1a3be646f84269\`.
- **H_GRONINGEN**, GKA/INBO UvA-BiTS (Movebank 922263102),
  pinned **current 2023 v7** Zenodo DOI 10.5281/zenodo.10053658
  (not old v5 10.5281/zenodo.6574736), published total **four animals**,
  source reference CSV MD5
  \`944d7d2488914b1b528b76812dea48f9\`.

Published official sources:
https://zenodo.org/records/10053583 and
https://zenodo.org/records/10053658.

The total **7 + 4 = 11** is an *optimistic upper bound* of candidate
individuals before any biological identity crosswalk, validation of
time/altitude covariates, within-bird repeat deployments or sample
support. The sites are two study clusters, not 11 proven independent
realizations of the ecological target process. Each study separately
has **fewer than ten individuals**, the minimum to allocate nine
calibration and one disjoint untouched validation bird under the
frozen single-stratum 90% rank design.

**MH_ANTWERPEN is not an unexamined external test set.** ODSP's frozen
September 2026 endpoint previously opened its GPS observations and
closed as \`empirical_state_prediction_unavailable\` because only
three individually admitted birds were available under that earlier
study design. Accordingly, the 3 marsh harriers and 1 buzzard
described by its archive are not added to this two-study new
candidate roster.

**Schlaich et al. (2017)** describe 29 *C. pygargus* GPS-tracked birds
and publish timestamps/lat/lon/speed, but their listed public
analysis files do **not** document an altitude outcome. They are not
eligible for this four-bin altitude-state transfer outcome. Schaub
et al. (2026) Dryad remains \`NOT_ADMITTED\` for the historical RF,
with potential reuse of regional tracking cohorts not ruled out.

## Source access chronology: first frozen v1 *failed a schema gate*

The narrow contract
\`research/BOP_TWO_MARSH_REFERENCE_ONLY_V1_CONTRACT.json\` was
committed at **\`e13490fa2c2c314e5129a32a7fa7b5f6e31a2897\`**
**before** either small source reference CSV was first inspected.
It whitelisted exactly two files, pinned their official published
MD5 values and explicitly forbade GPS, acceleration, altitude,
temperature and external observation outcomes.

On inspecting the published *reference headers* afterward, we
learned that the actual animal, species and tag ID fields are
\`animal-id\`, \`animal-taxon\` and \`tag-id\`.
The v1 contract had instead frozen
\`individual-local-identifier\`/\`individual-id\` and
\`individual-taxon-canonical-name\`-style aliases.
Therefore its outcome is **\`SOURCE_SCHEMA_HOLD\`**, not a retrospective
success. The first contract was not edited.

The separate
\`research/BOP_TWO_MARSH_REFERENCE_ONLY_V2_POSTHEADER_CONTRACT.json\`
states explicitly that the correct field names were observed
**before the correction**. The v2 source-only exercise is a **post-header
descriptive reconciliation**, not a fresh prospective validation
or a revision to the originally frozen experiment.

### One actual, scientifically useful identity trap

The published MH_WATERLAND reference preview shows **seven animal IDs
but only six tag IDs**: one transmitter/tag identifier was reused
on a different biological animal following the previous bird's
death. Counting tag identifiers as independent animals would
incorrectly combine two bird histories.

H_GRONINGEN's preview lists four animal IDs. The two sources'
visible animal-ID strings do not exactly overlap, but matching
strings are neither a complete cross-study identity crosswalk nor
proof that differently named birds are biologically distinct.

The provider's published MD5 values must still be checked against
the **actual original CSV bytes** before the source-only scripted
result is considered authoritative. Publication-page previews
are preliminary evidence, not cryptographic integrity checks.

## Reproducible read-only implementation

\`scripts/bop_two_marsh_reference_only_preflight.py\` downloads
**ONLY** these exact two public URLs:

- \`https://zenodo.org/records/10053583/files/MH_WATERLAND-reference-data.csv?download=1\`
- \`https://zenodo.org/records/10053658/files/H_GRONINGEN-reference-data.csv?download=1\`

It checks each download's size <=10 kB, redirects, MD5 against the
official source, and UTF-8 CSV schema. Raw individual, tag, nickname,
ring and deployment labels remain **in memory only**, without being
published or copied into a GitHub Actions artifact.

It reports only per-study source row counts, distinct
\`animal-id\` counts, distinct \`tag-id\` counts, number of tags used by
multiple animals, exact across-source animal/tag-ID string overlap
*counts*, and pinned source SHA256 values. It never reads position,
altitude or model outcome files.

It also emits these two separate scientific states:

1. **Original v1 terminal** \`SOURCE_SCHEMA_HOLD\`.
2. **Corrected post-header v2 descriptor**
   \`REFERENCE_ID_AND_TAG_REUSE_AUDIT_ONLY\`, with non-admission status
   \`HOLD_POPULATION_AND_IDENTITY_EXCHANGEABILITY_UNVERIFIED\`.

Even when the two CSV files have authentic MD5s and the **candidate
upper bound** is at least ten, the software must not issue a 90% future
animal coverage certificate. Two distinct study clusters are
insufficient to establish group-score exchangeability across
populations or a reliable study-level sampling distribution.

When either file is inaccessible, redirected unexpectedly, malformed
or checksum-mismatched, a first-run failure receipt is still retained
and no count or success is claimed.

## Test and non-duplication policy

\`\`\`bash
python -m pytest tests/test_bop_two_marsh_reference_only_preflight.py
python scripts/bop_two_marsh_reference_only_preflight.py --out /tmp/two-marsh-source-only.json
\`\`\`

No historic BOP, MH_ANTWERPEN or Schaub/Dryad GPS data are accessed;
their frozen results stay unchanged. These are necessary source
eligibility tests; **no new biological response is scored or calibrated**.
Do not use one dataset's animals as the new external target after
historically examining their response or silently combine source
clusters to achieve a positive rank number.

The scientific endpoint of the screen is a *real-data metadata
observation*: distinguishing re-used transmitters from biological
animals while refusing to promote cross-study group counts to
external predictive inference.
