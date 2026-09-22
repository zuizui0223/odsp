# ODSP method-surface freeze v1

The current CLI is larger than the intended long-term user surface. That is now
treated as technical debt, not as an invitation to add another route.

## Stable entry points

For ordinary use, the stable entry points are:

```text
odsp run
odsp transfer
```

One additional public namespace is visible:

```text
odsp experimental
```

It contains advanced governance/freeze operations rather than another ordinary
analysis route.

`run` executes a bundled reference learner under an explicit endpoint contract.
`transfer` starts after fitting and audits externally supplied held-out scores.
The population-level transfer summary is part of this existing transfer receipt;
it did not create another command.

## Frozen advanced compatibility surface

Eight legacy command spellings are retained because existing pre-outcome
contracts, semantic-freeze receipts and operating-characteristic qualifications
refer to them. They are executable but intentionally hidden from the ordinary
help surface.

The exact public surface is frozen in
`ODSP_METHOD_SURFACE_FREEZE_V1.json` and tested in CI: `run`, `transfer`,
and `experimental`. No fourth public top-level command should be added during
the rewritten N2 work.

This freeze does **not** revoke the inferential qualification of an existing
surface. It separates two questions:

1. whether an existing method has a valid frozen inferential role; and
2. whether that role deserves another public command.

The first can remain true while the second is now answered no.

## What may still change

Bug fixes, packaging, documentation, reproducibility repairs and corrections to
existing contracts remain allowed. Existing operating-characteristic
qualifications may be repaired if an error is found, but a repair must not spawn
a new inferential family or command.

The post-outcome population-transfer summary is descriptive and changes the
estimand reported by `transfer`; it is not a new familywise certification
variant.

## Deferred cleanup

The consolidation has already moved advanced governance behind
`experimental` and transfer families behind `transfer --variant`. After the
rewritten N2 and release stabilization, the hidden legacy aliases can be retired
through an explicit deprecation cycle. That refactor must preserve old receipts and
provide a deprecation/migration cycle rather than silently breaking frozen
contracts.

Until then, the rule is simple: **maintain the surface; do not grow it.**
