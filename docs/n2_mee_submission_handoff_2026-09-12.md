# N2 MEE submission-system handoff — 2026-09-12

This handoff separates **copy-ready non-personal submission metadata** from **author-only confirmations that must remain unresolved until the author team supplies or approves them**.

Canonical machine-readable packet: `N2_MEE_SUBMISSION_HANDOFF_PACKET.json`.

## Ready to copy into the submission system

The packet is regenerated from the existing validated v4 manuscript builder and title-page template. It contains:

- journal and article type;
- manuscript title and running headline;
- the submission-facing 350-word, four-part abstract;
- the eight manuscript keywords;
- paths to the anonymous review manuscript, anonymous code bundle, separate title page, cover letter and disclosure drafts;
- the frozen MH_ANTWERPEN and BOP_RODENT terminal categories.

The packet deliberately does **not** infer or prefill author names, authorship order, affiliations, correspondence details, CRediT roles, funding, conflicts of interest or approvals.

## What is now mechanically complete

The v4 submission package, anonymous review-code bundle and anonymous review DOCX have been built and validated in CI. The DOCX uses single-column layout, double line spacing, continuous body line numbering and page numbering; a corrected 25-page render also passed full-page development visual QA. These checks do not replace the corresponding author's final inspection of the exact files uploaded to the journal system.

## Remaining author-only gates

The submission must remain blocked until the author team confirms:

- final authorship and order;
- affiliations and addresses;
- corresponding-author details;
- all-author approval and no concurrent submission;
- final CRediT roles and the named author accountable for AI-assisted code/text review;
- acknowledgements, funding and conflict-of-interest wording;
- reuse terms or permission for every third-party dataset used;
- final data-availability, ethics and generative-AI wording;
- the optional translated-abstract decision;
- final visual approval of the exact upload files;
- entry and verification of metadata in the journal submission system.

## Scientific boundary

This handoff is administrative extraction only. It does not modify the v4 scientific manuscript, rerun an empirical endpoint, alter any frozen decision rule, relax the BOP mixed terminal state, rescue the MH unavailable endpoint, or promote N2 output to N3.
