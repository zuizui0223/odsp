# N2 MEE submission-positioning refresh — 2026-09-12

This update is editorial and administrative only. It does **not** change the validated state-prediction manuscript science, rerun any empirical endpoint, alter any frozen decision rule, or reopen N2→N3 promotion.

## Why this refresh was needed

The current *Methods in Ecology and Evolution* Research Article guidance emphasizes that a submission must describe a methodological contribution that is broadly applicable, should validate new computational methods with simulations or benchmarks before empirical application, and should not be merely a workflow linking existing methods. The journal also screens for a methodological gap that is broader than one focal taxon or case study.

The N2 v4 manuscript already satisfies the substantive structure:

- the methodological gap is stated independently of any focal organism;
- the prediction target is `P(A|X)` over explicit ecological states;
- the comparator is the lower-information training marginal `P(A)`;
- the primary evidence is independent-group held-out log-score gain;
- independent groups are not pooled to rescue conflicting failures;
- known-truth validation precedes empirical application;
- the finite-discrete information layer has broad representation-invariance tests;
- empirical endpoints retain unavailable and mixed outcomes rather than being retuned.

The main desk-screening risk was therefore **positioning**, not missing analysis: because random forests and multinomial regression are used as demonstration learners, an editor could misread the paper as a workflow connecting existing algorithms.

## Positioning change

The cover letter now states explicitly that the methodological contribution is not the choice or chaining of upstream prediction algorithms. The contribution is the learner-agnostic prediction-and-evidence object:

1. an explicit ecological-state distribution target `P(A|X)`;
2. a lower-information comparator `P(A)` estimated from the same training information;
3. group-preserving held-out transfer gains;
4. a predeclared fail-closed terminal distinction among generalizing, non-generalizing, mixed and unavailable outcomes; and
5. an information-theoretic separation among added-state thickness, fitted organization and independent predictive transfer.

Random forest and multinomial regression are therefore replaceable demonstration engines rather than the novelty claim.

## Submission-policy refresh

The v4 submission checklist was rechecked against the journal guidance on 2026-09-12. The administrative surface now explicitly records:

- separate title page for a double-anonymous submission;
- single-column, double-spaced manuscript with continuous line and page numbering;
- numbered 1–4 abstract at or below 350 words;
- anonymous code/data availability for peer review;
- explicit data-sources section on the title page;
- generative-AI application and model version disclosure;
- final author confirmation that every third-party dataset is publicly reusable or used with permission;
- cover letter as optional rather than a scientific requirement.

## Data reuse status

The primary BOP_RODENT Zenodo record is CC0. Public LifeWatch/IMIS metadata for MH_ANTWERPEN likewise records CC0 reuse status. Snapshot Serengeti is a public Dryad dataset; Dryad datasets are released under CC0 unless otherwise indicated. Tawaki and the Tadarida teniotis Movebank record remain supporting diagnostic sources; their final source-specific reuse terms are deliberately retained as a manual submission gate rather than being inferred automatically.

No original tracking or camera-trap source data are redistributed in the submission package as newly authored data.

## AI and ethics

The title-page and disclosure drafts already name OpenAI ChatGPT and the model version GPT-5.6 Sol. At least one named author must still explicitly accept responsibility for reviewing and validating all AI-assisted submitted code/text.

The present study performs no new animal capture, handling, manipulation or field sampling. It reanalyses archived datasets. Final approval of the wording about source-study ethics and permits remains an author gate.

## What remains manual

The technical/scientific package is ready for author metadata completion, but submission must remain blocked until the author team confirms:

- author list/order, affiliations and corresponding-author contact;
- all-author approval and no concurrent submission;
- final CRediT roles and the named AI-accountable author;
- acknowledgements, funding and conflict of interest;
- final reuse terms/permissions for every third-party source;
- final data-availability, ethics and AI wording;
- optional translated-abstract decision;
- ScholarOne metadata;
- final rendered-file compliance (double spacing, continuous line numbers, page numbers).

The residual decision whether the paper is sufficiently novel for *Methods in Ecology and Evolution* remains an editorial judgment. This refresh reduces avoidable framing risk but does not convert journal fit into a certified outcome.
