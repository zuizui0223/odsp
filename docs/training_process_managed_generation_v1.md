# Managed training-process generation v1

The existing process freeze fixes what should be sampled, and the existing
generation receipt can bind model bytes to a caller-declared schedule. That is
useful provenance, but it still permits a gap: the caller can declare that a
model came from a particular bootstrap membership and fit seed without ODSP
having observed the fitting invocation.

The managed-generation route closes that operational gap.

For each frozen refit, ODSP reconstructs the exact bootstrap membership from the
frozen source roster and resample seed. The canonical membership digest must
match the digest already stored in the process manifest. ODSP then invokes one
predeclared argv array with shell execution disabled. The argv must expose the
refit ID, membership file, fit seed and output directory explicitly.

Before the first fit, the runner records the Python runtime, installed
distribution versions, and only the explicitly allowlisted environment
variables. Every expected output artifact is predeclared and content-hashed.
stdout and stderr are retained only by digest in the receipt.

This makes the provenance claim substantially stronger: exact inputs were
materialized, exact frozen code was invoked with those inputs, and exact output
bytes were produced in the recorded environment.

It still does not turn semantic correctness of arbitrary fitting code into a
cryptographic fact. A frozen script can in principle ignore an argument. That
remaining boundary is auditable source behavior and is reported explicitly
rather than hidden.

No validation outcome is needed or allowed during managed generation.
