# Froidevaux original table v2 — PMC OAI-PMH JATS source admission (2026-11-23)

**Separately opened access route after terminal Europe PMC v1 HTTP500**. The original Europe PMC v1 receipt remains terminal SOURCE_STOP (Actions #45078238459, artifact #14776096892), not relabelled as a successful replication. This new retrieval uses the official NCBI PMC **OAI-PMH fulltext JATS API**, which PMC documents as an authorized automated access method. See https://pmc.ncbi.nlm.nih.gov/tools/oai/. This is still an already published, search-inspected 2014 Table 1, not a blinded scientific analysis. No new model parameters, taxon filtering or data-derived selection.

Exact requested original article: `oai:pubmedcentral.nih.gov:4278821`, `verb=GetRecord`, `metadataPrefix=pmc`. Endpoint:
`https://pmc.ncbi.nlm.nih.gov/api/oai/v1/mh/?verb=GetRecord&identifier=oai%3Apubmedcentral.nih.gov%3A4278821&metadataPrefix=pmc`.
Retrieve once per run; require OAI-PMH `GetRecord` record `metadata` containing one full-text JATS `article`, or STOP. Reject OAI errors and missing or wrong DOI `10.1002/ece3.1296` if present. Preserve the original whole-API response SHA256, byte length and PMC article ID as source fingerprints. Only official PMC metadata may serve as the source. No author-hand transcription or web snippets as synthetic source substitution.

Parse the same caption-named **original published Table 1** via prior `scripts/froidevaux2014_original_vertical_table_v1.py:parse_primary_table`; strip XML namespaces in memory only to make it compatible with namespaced OAI envelope. Require exactly 16 original taxon/sonotype rows, count columns gap, ground, canopy and per-row total, source sums **52,547, 41,850, 35,630**, and grand total 130,027. Reject any error; do not invent missing fields.

The fixed *descriptive* ecological target and claim ceiling are **unchanged** from `docs/froidevaux2014_independent_forest_table_contract_v1.md`: detected forest-ground vs forest-canopy `I(Taxon;recorder layer)`, `H(layer)`, `I/H(layer)`, plus original-author dominance sensitivity excluding *Pipistrellus pipistrellus*. These counts are already visible in a published table; there is **no plot- or site-heldout prediction** and no species×layer q calibration. If OAI service errors/denies article XML, retain source STOP and do not simulate a new ecological outcome.

No revisions of old frozen N2, batter JAE, or v4/v6 Gomes estimates.
