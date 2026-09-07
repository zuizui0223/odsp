# Held-out row alignment

ODSP validation layers often require the same untouched held-out rows, but equal vector lengths do not establish row identity. `odsp.heldout_row_alignment.audit_heldout_row_alignment` provides an optional machine-checkable provenance layer when callers can supply stable unique row keys.

The caller declares one canonical `base_row_ids` sequence and a named row-key sequence for every evidence source. The audit returns one of three categories:

- `exact_alignment`: every source contains the same unique rows in the base order;
- `reorderable_alignment`: every source contains the same unique rows, but at least one source uses a different order;
- `row_mismatch`: at least one source is missing rows, contains extra rows, or repeats a row key.

For an exact or reorderable source, `permutation_to_base` contains source indices in canonical base order. `reorder_validation_rows` can apply that verified permutation to a one-dimensional vector or to a selected axis of a multidimensional array, including refit-by-validation-row gain matrices.

The layer never guesses identity from numeric predictions, gains, group labels, or row contents. It never silently drops, duplicates, imputes, or matches nearest rows. A duplicate canonical base key is rejected because there is no unique target ordering.

This closes only a provenance gap. Matching caller-supplied row keys does **not** prove that the rows were truly untouched, that train/test separation was respected, that observations are independent, or that a biological block definition is correct. Those remain upstream scientific and data-pipeline responsibilities. No aggregate confidence score is emitted.
