# Training-source v0 provenance: outer source draw and nested refits

The v0 statistical target adds one upstream stochastic level above qualified v5.
Its provenance therefore cannot be represented by a flat list of refits.

The frozen empirical source roster remains the **sampling frame**. An outer
source draw is a stratified bootstrap draw from that roster. It is not described
as a newly collected ecological sample.

For each outer source draw, inner refits are then sampled from the empirical
distribution defined by that draw. Operationally, ODSP can reconstruct a
deterministic expanded list of source-draw slots from the outer membership
counts and bootstrap those slots with the frozen inner seed.

Both outer and inner memberships are reduced back to counts over the original
frozen roster:

```text
stratum | unit_id | count
```

including zero-count units. This gives a single canonical identity namespace and
allows both levels to be content-digested.

The manifest freezes:

- source roster file and semantic hashes;
- outer source-draw IDs and seeds;
- outer membership digests;
- a balanced inner-refit schedule within every outer source draw;
- inner resampling and fitting seeds;
- inner membership digests;
- generation/fitting implementation artifacts and fit parameters.

A later managed-generation layer must reconstruct every membership from the
frozen seeds before fitting and bind the resulting model bytes. The manifest by
itself is a plan, not execution evidence.

For validation separation, the entire **original source roster** must be
disjoint from validation. Checking only the source or inner draws that happened
to be realized is insufficient, because a different future draw from the
declared process can select any unit in the original frame.

This remains process-defined inference. It does not establish sampling from an
unknown ecological superpopulation.
