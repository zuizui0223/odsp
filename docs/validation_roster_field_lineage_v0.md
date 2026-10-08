# Validation roster *source-field lineage* preflight v0

## Scientific reason

ODSP already has sophisticated validation contracts: exact external row IDs,
group/block/weight metadata, complete source-frame separation, managed model
generation/scoring, source and runtime hashes, and strict declared
pre-outcome freeze/first-outcome access chronology.

Those are necessary checks, but neither content hashes nor freezing a CSV
prove that the values *inside* that CSV were generated without access to
the observations used as validation outcomes.

SNAPSHOT USA 2024 provides a concrete public counterexample. The public
Dryad dictionary describes Start_Date and End_Date as dates of camera
placement and retrieval. But Rooney et al. (2026, DOI
10.1111/geb.70229, PDF p.8 of 28, Data Cleaning) state that the
distributed deployment dates were changed to match the first and last
photographic observations. Survey_Nights similarly uses first/last
photo timestamps. Therefore a rule that selects sites based on the
distributed date fields incorporates observation-derived information
even when the dataset is frozen before its *analyst* accesses detection
labels.

This source-field dependence is different from conventional model leakage
through row overlap. It can change the external validation site's
inclusion probability in ways linked to the observation process.

The resulting methodological question is:

> Which upstream variables and transformations determined the held-out
> population before it was scored?

## Implemented design

The experimental opt-in numerical surface is
odsp.validation_roster_field_lineage_v0.audit_validation_roster_field_lineage_v0.

It takes a JSON-like field DAG. Every field declares:

- name, origin type, parent field names;
- whether its value was ever *corrected using observations*;
- a source-documentation statement (not a certificate);
- a mapping from actual validation-selection roles to those fields.

The REQUIRED roles are roster_membership, validation_group,
validation_block and sample_weight. Optional roles are
eligibility_filter, physical_unit_id and fold_assignment.
Missing required roles, unknown ancestor nodes, cycles, unsupported
field origins, and fields with nonsensical root/derived structure
raise errors.

Four origin labels are supported:

- design_recorded: claimed independent recording or prospective design;
- derived: deterministic processing with explicit upstream parents;
- observation_derived: a value calculated using the outcome process;
- unknown: provenance insufficient to establish independence.

Starting from every field that really influences the validation roster,
the checker traverses ALL upstream parents and propagates two kinds of
warnings:

1. observation-derived field or observation-based correction:
   HOLD_OUTCOME_DERIVED_SOURCE_METADATA;
2. unknown or undocumented source:
   HOLD_UNDOCUMENTED_SOURCE_METADATA_LINEAGE.

A field not used by the roster, groups, blocks, weights or eligibility
does not automatically contaminate the roster merely by existing in
the same raw file. Conversely, an apparently innocent derived interval
inherits the contamination of any parent.

### Synthetic, publication-grounded fail case

examples/validation_roster_lineage/snapshot_usa_photo_corrected_hold.json
encodes:

    first_photo_date  [observation_derived]
           |
     curated_start_date [outcome-corrected]
           |
        date_span
           |
        selected_site
           |
     roster_membership

The analogous last-photo route also feeds date_span. The preflight
returns HOLD_OUTCOME_DERIVED_SOURCE_METADATA, identifying the affected
role and dependency paths without reading any real animal outcomes.

### Synthetic declared-clean case

examples/validation_roster_lineage/hypothetical_predeclared_site_plan.json
uses a hypothetical physical camera allocation recorded independently
of detections, and weights derived only from its original sampling
probabilities. Outcome fields can exist in that broader source but do
not feed the site roster. It returns

    DECLARED_INDEPENDENT_LINEAGE_ONLY_NOT_ATTESTED.

This is **not approval** for primary ecological inference. The program
cannot check whether the user-provided human origin statements are true,
whether a documentation URL accurately describes the actual file,
or whether the sites themselves were iid sampled. Such proof needs
original auditable dated field logs, a defensible sampling protocol
and, ideally, independently verifiable source-system evidence.

## Confidence levels must not be collapsed

This new preflight separates:

- byte/content integrity (the file or declaration has not changed);
- chronological integrity (the analysis freeze predates *declared* access);
- generative independence (the values were not calculated or edited
  using observation outcomes);
- ecological sampling design (the units were valid independent draws).

The first two can be partly machine checked from hashes/timestamps.
The third is screened by this declared dependency DAG, but its
documentary truth requires external validation. The fourth remains
a separate design/statistical question, not settled by field lineage.

A clean result carries explicit false flags for trusted source-lineage
attestation and independent observation-value verification. It never
registers a new ODSP primary route, and makes no claim about a
new ecological population.

## Governance

This is a NEW optional route on an isolated branch. The qualified v5
process-mean route, outer source-process v0, fixed-set results and
historical empirical terminal decisions are not modified or
retrospectively reclassified.

Before promoting an ACTUAL new external ecological study, freeze its
field DAG (including the origin of row *membership* itself), original
source/validation sampling frames, score semantics and external
provenance. Reject source metadata containing observation-derived
eligibility even if the model fitting code has never seen the labels.

Source-method evidence:
- Rooney et al. 2026, DOI 10.1111/geb.70229, PDF page 8, source date editing.
- Dryad DOI 10.5061/dryad.bnzs7h4qf, variable dictionary.

This source-semantics failure mode is a useful methodological lesson,
but identifying one failure mode is not the same as showing a new
ecological causal mechanism or a high-impact empirical discovery.
