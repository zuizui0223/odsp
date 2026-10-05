# Untouched external validation for the training-process v5 route

This route is deliberately separate from the existing fixed-set external
endpoint. The target remains the mean held-out directional gain over the frozen
training-resampling process, conditional on the frozen training source.

Before external score values are available, the freeze generator reads an
outcome-free roster containing exactly:

- row_id
- group_id
- block_id
- sample_weight

Those four fields define the validation sampling design. They are canonicalized
and content-hashed before outcome access. Group, block or weight definitions
therefore cannot be changed after seeing external scores.

The freeze also binds the training-process manifest, managed-generation receipt,
complete refit identity, information filtration, score semantics, inferential
settings, qualification evidence, endpoint implementation source closure and
runtime dependency identity. The complete frozen training source frame must
already be disjoint from the external row roster.

At runtime the outcome-bearing table contains only row identity, refit identity
and the predeclared score columns. It must form the exact frozen row x refit
Cartesian product. Group, block and weight metadata are taken only from the
pre-outcome freeze.

After semantic verification, the endpoint reconstructs aligned refit-by-row
score matrices and calls the qualified provenance-verifying v5 internal wrapper.

The endpoint does not prove historical non-access to external outcomes, nor does
it prove that supplied score values were mechanically produced by the frozen
model artifacts. Those limits remain explicit.
