# Block-definition sensitivity audit

`odsp.block_definition_sensitivity.audit_block_definition_sensitivity` reruns the existing block-aware transfer uncertainty audit under multiple caller-declared plausible block definitions on the **same held-out rows**.

Use it when the scientifically defensible independence unit is not unique—for example, day versus bout versus deployment. ODSP does not choose a preferred definition and does not infer the true independence structure. It asks whether the transfer conclusion changes across the supplied definitions.

The output preserves each definition's full block-aware audit and reports a summary category:

- `block_definition_robust_generalizing`: every supplied definition is robustly positive;
- `block_definition_robust_non_generalizing`: every supplied definition is robustly non-positive;
- `stable_unavailable`: every supplied definition has too few blocks;
- `stable_<category>`: every definition agrees on another block-aware category;
- `block_definition_sensitive`: at least two supplied definitions yield different robust-transfer categories.

A large number of rows cannot rescue a block definition with too few independent blocks. Likewise, stability across supplied definitions does **not** prove that any supplied block definition is biologically correct; it only demonstrates stability over the declared sensitivity set.

The frozen known-truth benchmark includes a pseudoreplication case where treating every row as independent produces a robust-positive interval while an eight-cluster definition makes the same positive point estimate uncertain. Strong positive and negative signals remain stable across fine and coarser admissible block definitions.
