# Untouched external training-process route v2: managed score provenance

External v1 closes the statistical and semantic-freeze chain but deliberately
reports one remaining provenance gap: it accepts a score table without proving
that the table was produced by the frozen model artifacts.

V2 closes that operational gap before the external route is eligible for
registration.

Before outcome access, the external freeze now also binds a scoring execution
plan: an argv array, scoring implementation artifacts, working directory,
timeout, environment allowlist and the exact expected score columns. No external
outcome value is read during this freeze.

After outcome access, ODSP performs managed scoring. For every frozen refit it:

1. re-hashes the generated model artifacts against the managed-generation
   receipt;
2. verifies that the outcome-bearing external data have exactly the frozen row
   roster;
3. invokes the frozen scoring argv with shell execution disabled, explicitly
   passing the refit ID, refit model directory, external data path and output
   path;
4. requires the output to contain exactly the frozen rows and score columns;
5. hashes stdout, stderr and the score artifact; and
6. assembles the canonical row x refit score table itself.

The external inferential endpoint accepts only that managed score artifact
together with the exact managed-scoring receipt SHA256.

As with managed fitting, this proves exact operational provenance rather than
semantic correctness of arbitrary code. A frozen scorer could deliberately
ignore an argument; that is an auditable source-code property, not something a
hash can mathematically exclude.

External v1 remains as development provenance but is not eligible for primary
route registration.
