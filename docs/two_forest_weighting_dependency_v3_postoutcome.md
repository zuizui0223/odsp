# Weighting-dependent species × recorded-layer information across two original bat acoustic datasets (v3, post-outcome; 2026-11-23)

## Evidence status

This is a **transparently post-original-outcome descriptive contrast**, NOT an independent confirmation after an unopened source. The original published Swiss Table 1 and original 2020 Gomes count responses have already been viewed. No model/parameter/significance claim is preregistered as untouched; no new p-values or heldout predictions are generated.

Independent sources and official byte verification:
- **Temperate Swiss forest**: Froidevaux et al. (2014), DOI `10.1002/ece3.1296`, fulltext PMCID PMC4278821 original **NCBI OAI-PMH JATS** source authenticated by run [#45078501629](https://github.com/zuizui0223/odsp/actions/runs/45078501629), artifact 14776441408, OAI response SHA256 `6da2280f01723b426795ba174fbf3b0050f9fb1cfcbd0e7538b05744750b8ffb`. Source: 16 published taxon names, total three-habitat n=130027, ground=41850, canopy=35630. 32 plots in 8 landscape cells, but source Table 1 pooled everything and provides no independently held-out plot or night.
- **Tropical French Guiana**: Gomes et al. (2020), `10.5281/zenodo.4019867`, original `Bats.csv` SHA256 `4a3b84e7175c29110bb6220f5cdf5889152897501b371fad3e2d9a74523773c9` (MD5 `2bc125dd0021d23c0efa0cb80828c632`), source original 7854 structured rows and 16,123 positive and zero pass-count totals; original-author rule `sum(Number)>5` selects 17 acoustic labels, 16,115 recordings. Original v4 conditioned information `I(Bat;POS|HOUR)=0.17613038` nats with 8/9 day transfers positive but 95% interval containing zero; local two-tower transfer 2/2 positive, 180m apart. Neither is an independent geographical SDM result.

**Do not compare published Swiss unconditional I to the earlier Gomes conditional-on-HOUR I**: they answer different questions. This v3 works with a harmonized *unconditional* observed two-layer target for both sources, and explicitly calls it a **recording-level contrast**, not true animal flight height or a multispecies niche distribution over x-y/z.

## Fixed descriptive measures

For each original source and fixed class roster:
1. Use only **recorded ground/canopy** (Swiss) or **recorded below/above** (Gomes); ignore Swiss gap because not equivalent to a second vertical layer. Count each original Swiss published **sequence** once by recorded taxon/layer, and each Gomes original acoustic **Number** once by original class/recorded position (do not count CSV source rows).
2. **Mass-weighted** original observed information: `p(S=s,Z=z)=n_sz / N`, `I_mass=Σ p_sz log[p_sz/(p_s p_z)]`, `Hmass(Z)`, ratio `I_mass/Hmass(Z)`. Report number of *source labels* and separately number of *active labels with ground+canopy >0*. A taxon with only Swiss gap sequences has no contribution to the two-layer information and must **not** be treated as a true absence, an active species or a zero-weight valid macro label.
3. **Taxon-equal information**: for every acoustically active label, `q(z|s)=n_sz/(n_s,above+n_s,below)`, define `p_equal(s,z)=q(z|s)/K_active`. Compute `I_equal=Σ p_equal(s,z) log[p_equal(z|s)/p_equal(z)]`, `H_equal(Z)`, fraction `I_equal/H_equal(Z)`. This is a clearly labeled counterfactual **equal acoustic-label importance**, not the fraction of underlying bat individuals or corrected biological diversity. Report `K_active` and effective mass-weighted class number `exp(H_mass(S))` for context. No pseudocount in original I; log(0) terms contribute 0 by limit.
4. **Predeclared descriptive sparse-group guard**: recompute equal-label I **only** on labels with >=20 observed ground+canopy recorded counts, using the same threshold in both sources; report class counts, no new test, and never substitute this sensitivity for primary I. Retain all original categories in the mass-weighted primary.
5. **Original published ecological dominance guard (Swiss only)**: also show original author excluding *Pipistrellus pipistrellus* from guild activity due >87% sequences, with all same measures (including K_active). This is a distinct target and not the primary community-level result. Original Table 1 has a *gap-only* taxon, which must be accounted for separately.
6. If two source libraries disagree on exact original primary count sums or original body files, STOP. The official NCBI original fulltext and original Zenodo v1 source are freshly checked; original checksum/size and publication DOI are matched.
7. No statistical sign test: taxonomy across sources is not shared and the Swiss data are already pooled. This is *not* cross-biome transfer of species strategy or an identified detector q. Positive MI may arise from species×microphone detectability interaction; unknown q remains explicit.

## Research implication and claim ceiling

The contrast tests a mathematical/ecological *estimand* point: when a single abundant broad-use taxon dominates acoustic recordings, `I_mass` may be near zero even though some uncommon detected classes have substantial differences in layer profiles. Equal acoustic-label weighting answers a different conservation/diversity target and can expose this otherwise hidden pattern, but can exaggerate unstable preferences of rare classes; the >=20-count diagnostic must stay visible.

What may be said: a **reference-measure dependence of observed horizontal projection loss** can be quantified from original published temperate and tropical acoustic tables. Not allowed: claiming unseen-plot predictive superiority, true bat vertical niche partition, corrected flight height/AGL, cross-species behavioral transfer, causal competition, or global ecological law based on these two observational sources.

Original frozen ODSP N2, ESDM E5 and batter JAE releases remain untouched. PR #306 stays Draft.
