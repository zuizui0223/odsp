# N2 MEE scientific review distribution boundary

The ODSP development repository contains two different surfaces and they should not be conflated.

## Scientific peer-review surface

The double-anonymous MEE review archive is built by `scripts/build_n2_mee_review_bundle_v4.py`. It is **whitelist-based**: only the scientific information/thickness/transferability/state-prediction modules, selected scientific tests, frozen public-data runners, anonymous manuscript material and sanitized evidence summaries are copied into the archive.

It intentionally excludes:

- Git history;
- `.github` workflows;
- PR and workflow provenance;
- `forecast_assessment` v1-v11;
- access-ledger/checkpoint/provenance audit machinery;
- trust-dossier / robust-model-selection infrastructure;
- author-identifying submission administration.

The development repository is therefore **not** the peer-review code distribution.

## Why not split the Python package immediately?

A package/repository split immediately before submission would create a second scientific source tree, new versioning and synchronization obligations, and risk changing a validated review artifact for no scientific benefit. The existing review archive already provides the separation reviewers need.

Instead, `N2_MEE_REVIEW_DISTRIBUTION_BOUNDARY.json` now makes the scientific surface explicit and `scripts/audit_n2_mee_review_distribution.py` fails closed if an undeclared ODSP module or a governance/internal path enters the review ZIP.

This is a distribution boundary, not a claim that governance code is invalid or should be deleted. Governance/provenance machinery can remain in the development repository without being presented as part of the manuscript method.

## Submission implication

Reviewers should receive the anonymous scientific bundle, not a checkout of the full development repository. A future accepted-code archive can decide separately whether to publish the governance infrastructure alongside, in a separate archival component, or not at all.
