# Beyond flat niche maps: separating added-axis thickness from transferable ecological organization

**Manuscript type:** Research Article  
**Target journal:** Methods in Ecology and Evolution  
**Review draft:** anonymized working version

## Abstract

1. Ecological niches and distributions are commonly represented on horizontal maps, although organismal use can also vary with height, depth, time or other ecological state axes. Adding dimensions to a fitted representation, however, does not by itself show that the lost state structure is estimable, organized or independently generalizable. We therefore need to separate the magnitude of projection loss from the transferability of the organization that produces it.

2. We introduce an information-theoretic framework for non-negative ecological support tensors. Added-axis thickness is measured by conditional information `H(A|B)` and its effective state count `exp(H(A|B))` after a declared base state `B` is known. Fitted organization is kept distinct from held-out transferability, which is scored as `E[log P_model(A|B) - log P_model(A)]` against an explicit marginal comparator. Prospectively independent groups are scored separately, with cross-fitting when each held-out group requires its own training support. Analytic known-truth families and concealed finite-observation benchmarks test thick-but-unorganized, stable-generalizing and shifted-non-generalizing states before empirical application.

3. Three prospectively bounded empirical lanes occupied different inferential states. A Tawaki GPS-dive design was structurally unavailable before biological thickness was opened. European free-tailed bat tracking retained substantial vertical thickness after horizontal location was known (`H(Z|X,Y)=1.392` nats; 4.02 effective states), but both sealed-individual conditional-versus-marginal gains were negative. In contrast, Snapshot Serengeti camera detections were temporally broad within sites (`H(T|Site)=1.640`; 5.15 of six effective time states), showed species-time partitioning (`I(Species;T|Site)=0.224`, permutation `p=0.005`), and had positive gains in all three independently held-out site folds.

4. Projection loss therefore has at least two empirically separable components: how much added-axis state remains after projection and whether the organization of that state transfers to independent observations. Treating estimability, thickness, organization and transferability as separate inferential layers prevents descriptively rich multidimensional fits from being promoted automatically to generalizable ecological structure. The framework is axis-agnostic, while biological interpretation remains explicitly tied to the observation semantics of each added dimension.

**Keywords:** ecological niche; information theory; projection loss; transferability; cross-validation; multidimensional ecology; vertical niche; temporal niche

## Data and code for peer review

All analyses are implemented in an open-source Python package under the MIT License. For double-anonymous review, the code, machine-readable analysis contracts, synthetic benchmarks and terminal result receipts will be provided in an anonymized review archive. The empirical source datasets are publicly archived by their original data providers: Tawaki dive and tracking data through the project repository and Zenodo archive associated with Otis et al. (2025), European free-tailed bat tracking through the Movebank Data Repository archive associated with O'Mara et al. (2021), and Snapshot Serengeti camera-trap consensus and effort data through Dryad associated with Swanson et al. (2015). No empirical source data are redistributed as newly authored data in this repository.

> **Submission note to finalize:** Methods in Ecology and Evolution currently requires disclosure of large-language-model use when applicable to work described in the manuscript. The final submission should include the required disclosure with the application/version and author responsibility wording used by the journal at submission time.

# 1. Introduction

Ecological niches are fundamentally multidimensional concepts. Hutchinson's n-dimensional hypervolume formalized a niche as a region in environmental state space rather than as a geographic surface (Hutchinson, 1957), and modern computational approaches have made high-dimensional niche geometry directly estimable for many ecological applications (Blonder et al., 2014). Yet most ecological decisions are still communicated through lower-dimensional products: maps of habitat suitability, occupancy, use, overlap or predicted distribution. Such products are often useful and appropriate. The inferential difficulty is that a map is a marginal projection of a potentially richer ecological state space. Organismal support at the same horizontal location can vary with height, depth, time, season, life stage, behaviour or other state axes, and that structure can disappear when the added axes are collapsed.

The existence of a multidimensional fitted representation does not, by itself, resolve the status of the lost structure. At least four questions are distinct. First, is the added axis actually estimable under the observation architecture available for the study? Second, if it is estimable, how much state information remains along that axis after the retained or mapped state is known? Third, is the added state systematically organized with respect to location, identity or another declared conditioning state? Fourth, does that organization improve prediction in prospectively independent data relative to a lower-information representation that ignores the conditioning structure? These questions correspond to **estimability, thickness, organization and transferability**. Treating them as one claim can make a descriptively rich multidimensional model appear more general than the evidence warrants.

This distinction is closely related to the long-standing problem of ecological model transferability. Predictive performance within a reference data set does not guarantee performance in another region, period or population (Wenger & Olden, 2012; Yates et al., 2018). Validation design matters because randomly partitioned data can retain spatial, temporal, hierarchical or phylogenetic dependence and thereby underestimate prediction error under genuine transfer (Roberts et al., 2017). Spatially or environmentally separated folds are now widely used to make ecological validation better match intended applications (Valavi et al., 2019), and explicit descriptions of reference and target systems are increasingly recommended for model transfer (Sequeira et al., 2018). Recent cross-continental evaluations continue to show that apparently satisfactory random-holdout performance can coexist with weaker transfer to genuinely independent regions (Matsui, 2026). For multidimensional niche inference, therefore, the relevant question is not simply whether an added dimension improves a fitted representation. It is whether conditioning on the proposed organization improves independent prediction over the corresponding marginal representation.

Here we develop a general information-theoretic framework for this problem. We represent ecological support as a non-negative tensor whose axes have explicitly declared meanings. For a retained or base state `B` and an added ecological state `A`, conditional entropy `H(A|B)` measures the amount of added-state information remaining after `B` is known, while `exp(H(A|B))` converts that information to an effective number of states. We treat fitted organization separately, using mutual-information quantities appropriate to the declared axes, and quantify held-out transferability as the expected log-score gain of `P_model(A|B)` over the lower-information marginal `P_model(A)`. Independent replication units are scored separately, so a large group cannot rescue a conflicting independent group merely by contributing more observations. When the validation design is cross-fitted, each held-out group is evaluated against a model trained without that group.

We validate this hierarchy before empirical application. Analytic known-truth families were constructed so that support can be thick but unorganized, stably organized, or organized in the fitted sample but shifted in held-out data. Concealed finite-observation benchmarks then test whether the intended quantities can be recovered under sampling. Finally, we apply prospectively frozen versions of the framework to three public empirical systems with different added-axis semantics and observation architectures. A Tawaki GPS-dive lane asks whether a vertical endpoint is structurally estimable before any biological thickness result is opened. A European free-tailed bat lane tests vertical thickness and cross-individual transferability using native same-event GPS height. A Snapshot Serengeti lane tests temporal thickness, species-time partitioning and cross-fitted transferability across independent camera-site folds. We allowed each lane to terminate as unavailable, non-generalizing or generalizing without post-outcome retuning. This design lets us ask whether thickness magnitude and transferable organization are empirically separable states rather than assuming that multidimensionality is a binary property.

# 2. Materials and Methods

## 2.1 Ecological support, projection and added-axis thickness

Let `S` be a non-negative array describing ecological support over declared state axes. The entries may represent weighted observations, model support or another explicitly defined support quantity, but the biological semantics of `S` must be declared before interpretation. We distinguish **species support** from **structural capacity**: an availability or habitat-state tensor is not relabelled as organism use, and an organism-support tensor is not interpreted as the complete set of available states.

Partition the axes of `S` into retained or base axes `B` and added axes `A`. After normalizing the eligible support to a probability distribution, projection onto the retained representation marginalizes over `A`. We quantify the state information removed by this projection as the conditional entropy

`H(A|B) = H(A,B) - H(B)`.

For a vertical axis `Z` and horizontal location `(X,Y)`, this gives `H(Z|X,Y)`. For time `T` within a site or another spatial context `B`, it gives `H(T|B)`. Multiple added axes can be treated jointly, for example `H(Z,T|X,Y)`. Conditional entropy is reported in natural logarithm units (nats).

For interpretation on a state-count scale, we use

`N_eff(A|B) = exp(H(A|B))`,

which is the effective number of equally probable added states corresponding to the observed conditional entropy. This quantity is a diversity-equivalent state count, not a count of occupied physical strata and not a probability of occupancy.

Where useful, the same calculation can be performed separately within each supported base-state cell to map local thickness. Conditional mutual information can likewise quantify dependence among added axes, for example `I(Z;T|X,Y)`. None of these quantities identifies causal interactions; they describe organization in the declared support distribution.

## 2.2 Fitted organization

Thickness magnitude and fitted organization answer different questions. A support tensor may contain several effective added states everywhere while having no association between the base state and the relative frequencies of those states. We therefore quantify generic fitted organization as mutual information between the declared base and added axes, `I(A;B)`.

For temporal partitioning among identities within context, we use conditional mutual information. If `C` denotes identity (for example species), `T` time state and `B` context (for example site), then

`I(C;T|B) = H(C|B) + H(T|B) - H(C,T|B)`.

This quantity measures conditional association between identity and time after context is known. It does not identify competition, temporal displacement or another causal process.

## 2.3 Held-out conditional-versus-marginal transferability

We define transferability by comparing the fitted conditioned distribution with its lower-information marginal in prospectively independent support. For model support and held-out support defined on the same declared axes, the mean held-out gain is

`G = E_heldout[ log P_model(A|B) - log P_model(A) ]`.

The marginal `P_model(A)` is not a null model chosen after outcome access; it is the explicit representation obtained by discarding the base-resolved organization whose transferability is being tested. Thus `G>0` means the added conditioning structure improves held-out log score relative to the model marginal, whereas `G<=0` means that it does not. Under the same generating distribution, the expected log gain corresponds to information supplied by the conditioning state, linking the score directly to standard information-theoretic identities (Shannon, 1948; Cover & Thomas, 2006).

The generic scoring core performs no implicit smoothing. If an empirical application requires pseudocounts or another regularization rule, that rule must be specified before the held-out outcome is opened. A model state with zero probability can therefore produce a negative-infinite held-out gain when the held-out support occupies that state, rather than being silently rescued by an unreported smoothing choice.

## 2.4 Independent groups and cross-fitting

A terminal generalization claim is based on prospectively independent replication units rather than on pooled observation mass. Let `G_j` be the gain for independent group `j`. At the zero-gain boundary used by the empirical analyses here, we classify transferability as:

- **generalizing** if every `G_j > 0`;
- **non-generalizing** if every `G_j <= 0`;
- **mixed** otherwise.

The arithmetic mean across groups can be reported descriptively but does not determine the terminal category. This prevents one large individual, year, site or instrument from dominating a conflicting independent group simply by contributing more observations.

When each held-out group has a different training set, we use cross-fitted grouped scoring. For group `j`, `P_model,j` is estimated without the support assigned to group `j`, and `G_j` is then computed on that held-out group. The group-specific scores are combined only through the predeclared sign-pattern rule above.

## 2.5 Known-truth validation

We first evaluated the framework using analytically known support arrays. These tests are methodological validation and are not empirical ecological evidence.

A **thick-unorganized** family contained four equally represented added states at every base state. It therefore had four effective added states but no base-added association. The expected `I(A;B)` and held-out conditional-versus-marginal gain were both zero.

A **stable-organization** family assigned added states in a 3:1 ratio in one base state and the reverse 1:3 ratio in the other. The held-out support was generated from the same organization. The analytic fitted mutual information and expected held-out gain were both

`0.75 log(1.5) + 0.25 log(0.5) = 0.13081203594113697` nats.

A **shifted-organization** family used the same fitted support but reversed the base-specific added-state organization in held-out data. Fitted mutual information therefore remained `0.13081203594113697` nats, whereas the analytic held-out gain was

`0.25 log(1.5) + 0.75 log(0.5) = -0.41849410839291784` nats.

Additional projection fixtures included vertically separated, temporally separated and joint-only separated support distributions with identical horizontal marginals, as well as independent and coupled vertical-temporal states. Concealed finite-observation benchmarks sampled counts from known support distributions to verify recovery under finite sampling.

## 2.6 Observation semantics and prospective empirical gates

Empirical interpretation requires that every axis correspond to an explicitly observed or defensibly linked state. For temporal information, source-reported biological observation time is preserved together with its precision and time-zone semantics. Upload, creation or modification timestamps are not substituted for observation time; date-only observations are not converted to ecological midnight; and a time zone is not invented at ingestion when the source does not supply one.

For vertical information, organism height or depth is distinguished from locality elevation, bathymetry, sensor placement and other contextual fields. A locality elevation does not become organism `Z`, and a sensor height does not become an organism vertical state. Missing or partial vertical and temporal state remains missing or partial.

Before each empirical outcome was opened, we froze the source identity, axis semantics, structural eligibility rules, state bins or categories, replication units, weighting, held-out definition and terminal decision rule in a machine-readable contract. A structural failure could terminate a lane as unavailable. Negative or mixed held-out results could not trigger changes to the primary state bins, spatial grain, data source or replication rule.

## 2.7 Empirical application 1: Tawaki structural estimability

The first empirical lane used public Tawaki (*Eudyptes pachyrhynchus*) GPS and dive data from Milford Sound, New Zealand, associated with Otis et al. (2025) and the archived data release (Zenodo DOI `10.5281/zenodo.14849008`). We linked the complete processed dive denominator to location-linked dive events under an exact, predeclared identity reconciliation. The target was a vertical depth axis within 5-km horizontal cells, with a deterministic whole-bird model/sealed assignment and a full site-by-year structural denominator.

This lane was explicitly a structural gate before biological thickness. The primary endpoint could proceed only if every frozen site-year stratum retained estimable cells under the predeclared minimum support requirements. If this condition failed, `H(Z|X,Y)`, local thickness and held-out biological scores were not opened.

## 2.8 Empirical application 2: European free-tailed bat vertical thickness

The second lane used the Movebank Data Repository archive underlying O'Mara et al. (2021), *Bats use topography and nocturnal updrafts to fly high and fast* (Movebank DOI `10.5441/001/1.52nn82r9`). The archive contains high-frequency GPS tracks for European free-tailed bats (*Tadarida teniotis*) with same-event horizontal coordinates, timestamps and native height above mean sea level. The primary vertical field was frozen as native `height_above_msl`; it was not converted post hoc to height above ground.

The primary horizontal grid was EPSG:3035 at 5 km. Vertical state edges were fixed at `[-inf, 0, 50, 100, 200, 400, 800, 1600, 3200, inf]` m. Structural eligibility was defined from the model pool before numeric height outcomes were opened. Six individuals formed the model pool and two whole individuals were sealed for the independent answer check.

To prevent individuals with more fixes from dominating, each model bat contributed equal total horizontal mass across its eligible events. Within a cell, each represented model individual received a Jeffreys-smoothed fixed-bin vertical distribution and `P_model(z|x,y)` was the arithmetic mean across represented individuals. The marginal `P_model(z)` was likewise the equal-individual mean of per-bat marginals. The primary support `P_model(x,y,z)=P_model(x,y)P_model(z|x,y)` was used for `H(Z|X,Y)` and effective vertical states. Each sealed individual received one mean gain `E[log P_model(z|x,y)-log P_model(z)]`. Both gains strictly greater than zero were required for a generalizing endpoint.

## 2.9 Empirical application 3: Snapshot Serengeti temporal partitioning

The third lane used the Snapshot Serengeti consensus camera-trap data and camera search-effort intervals (Swanson et al., 2015; Dryad DOI `10.5061/dryad.5pt92`). Source-reported Tanzania local clock time (UTC+3, without daylight-saving conversion) was retained. Repeated detections of the same species at the same site within 30 minutes were reduced to one independent event. Each retained event was weighted by the inverse number of merged valid camera-days at its site so that longer-running cameras did not dominate support.

Time was discretized prospectively into six fixed four-hour bins: 00:00–04:00, 04:00–08:00, 08:00–12:00, 12:00–16:00, 16:00–20:00 and 20:00–24:00. Species admission used only outcome-blind support criteria: at least 500 independent events, at least 20 distinct sites, and at least 50 events in each of three deterministic site folds. Site folds were assigned by `sha256(SiteID) modulo 3`.

For admitted species, we calculated `H(T|Site)` and `exp(H(T|Site))`. Species-time partitioning was quantified as `I(Species;T|Site)` and tested against 199 within-site permutations of species labels, preserving site-specific species counts and the observed temporal schedule (seed `20260903`).

For transferability, each site fold was held out in turn. The other two folds formed the training support, with a predeclared pseudocount of 0.5 for species-time cells. We then scored the held-out fold using `E[log P_model(T|Species)-log P_model(T)]`. All three fold gains had to be positive for the terminal category `temporal_partition_generalizing`, conditional on the permutation test detecting partitioning at `alpha=0.05`.

# 3. Results

## 3.1 Known truth separated thickness from organization and transferability

The analytic benchmark recovered the intended inferential states exactly. Thick-unorganized support retained four effective added states while both fitted base-added mutual information and held-out conditional-versus-marginal gain were zero. Stable organization produced fitted information and held-out gain of `0.13081203594113697` nats. Reversing that organization only in held-out support left fitted information unchanged at `0.13081203594113697` nats but changed held-out gain to `-0.41849410839291784` nats. Thus the same fitted multidimensional organization can correspond to positive or negative independent transfer depending on whether that organization persists beyond the fitted support.

Projection fixtures also recovered complete information loss in cases where horizontal marginals were identical but species or support distributions were disjoint along vertical, temporal or joint vertical-temporal states. These tests establish that a planar representation can be sufficient, partially lossy or completely misleading with respect to declared added-state organization, depending on the generating support.

## 3.2 The Tawaki vertical endpoint was prospectively unestimable

The Tawaki lane failed its frozen full site-by-year structural coverage requirement because Harrison Cove 2019 and 2020 contained no estimable primary cells under the predeclared structural denominator. The lane therefore terminated as `empirical_gate_d_unavailable`. No biological `H(Z|X,Y)`, local thickness map or sealed biological transfer score was opened.

This terminal state is not evidence that Tawaki lack vertical niche structure. It indicates that the particular prospectively defined empirical vertical claim was not estimable from the available linked observation architecture without changing the target after inspecting structural coverage.

## 3.3 European free-tailed bat support was vertically thick

Numeric vertical-state quality control passed for all 10,335 structurally linked tracking events (10,335/10,335 finite native height values). Eighteen 5-km cells met the frozen model-pool eligibility rule. Across this support, vertical conditional entropy was

`H(Z|X,Y) = 1.3918623004770097` nats,

corresponding to

`exp(H(Z|X,Y)) = 4.022333876564191`

effective fixed vertical states after horizontal location was known. Horizontal projection therefore discarded substantial descriptive vertical-state information from the model-pool support.

## 3.4 Bat vertical organization did not transfer to either sealed individual

The independent answer check reversed the interpretation suggested by thickness magnitude alone. For sealed Bat5, the mean gain of the location-conditioned vertical distribution over the model-pool marginal was `-0.43541033813280833`. For sealed Bat7, the gain was `-0.021938657402345435`. Both were non-positive, and the equal-individual mean was `-0.22867449776757687`.

The terminal category was therefore `empirical_n2_thickness_not_generalizing`. The model-pool support was descriptively vertically thick, but its detailed `P_model(z|x,y)` organization did not predict either independent bat's vertical state better than `P_model(z)`. Frozen 2.5-km and 10-km grid sensitivities and finer/coarser alternative fixed vertical bins were also non-generalizing; none was permitted to replace the primary result.

## 3.5 Snapshot Serengeti support was temporally broad and species-partitioned within sites

Seventeen mammal species passed the frozen outcome-blind admission criteria. Temporal conditional entropy within sites was

`H(T|Site) = 1.6396235816361795` nats,

corresponding to `5.153229376935854` effective four-hour states out of the six fixed temporal bins. Thus camera detections within sites occupied a broad portion of the source-local-clock temporal state space.

Species identity was associated with detected time after site was known:

`I(Species;T|Site) = 0.22427598739601606` nats.

Against the 199 within-site species-label permutations, the frozen p-value was `0.005`, the minimum attainable value under the plus-one permutation calculation with 199 null draws. The temporal partition was therefore detected under the predeclared `alpha=0.05` rule.

## 3.6 Serengeti temporal organization generalized across all three held-out site folds

All three cross-fitted site-fold gains were positive. The gains were `0.0572411993741857`, `0.045158861333215006` and `0.04514355468571751` nats per held-out event, respectively. Species-conditioned temporal distributions therefore improved prediction over the species-blind model temporal marginal in every prospectively held-out spatial fold.

Combined with the detected within-site partition, this yielded the terminal category `temporal_partition_generalizing`. The result is specifically a generalization statement about camera-detected source-local-clock-time organization across these deterministic site folds. It is not, by itself, evidence for causal temporal displacement, competition, solar-time partitioning or a universal activity-time niche.

## 3.7 Empirical lanes occupied three distinct inferential states

The three prospectively bounded applications occupied different positions in the inferential hierarchy. Tawaki terminated before biological thickness could be estimated. European free-tailed bat support was thick but its conditioned organization was non-generalizing. Snapshot Serengeti support was temporally thick, species-partitioned within sites and generalizing across every independent site fold.

These outcomes show empirically that projection loss cannot be summarized by a single binary label of “multidimensional” versus “not multidimensional”. At minimum, added-axis state magnitude and the independent transferability of its organization are separable empirical properties. A large conditional entropy can coexist with a failed independent answer check, while a different empirical system can satisfy both thickness and transferability criteria under the same general inferential logic.

# 4. Discussion

## 4.1 A thick fitted niche is not enough

The central practical result of this study is that multidimensional geometry can be descriptively real without being independently generalizable. The European free-tailed bat support retained approximately four effective vertical states after horizontal location was known, yet the location-conditioned vertical distribution performed worse than the corresponding marginal distribution for both sealed individuals. If inference stopped at `H(Z|X,Y)` or at a visually structured three-dimensional support map, this system could easily be described as having validated spatially organized vertical niche structure. The held-out answer check shows that this stronger statement was not supported.

This does not invalidate multidimensional niche geometry or hypervolume approaches. Those methods answer important questions about the shape, position and overlap of fitted ecological state spaces (e.g. Blonder et al., 2014). The distinction is instead inferential: **describing fitted geometry and claiming that its detailed organization transfers to independent observations are different tasks**. Conditional entropy is useful precisely because it quantifies projection loss without pretending to answer the second question. Transferability then becomes an additional evidential layer rather than a property assumed from descriptive richness.

The same distinction occurs throughout ecological modelling. Wenger and Olden (2012) emphasized that transferability must be evaluated separately from model performance in the reference system, while subsequent work has shown how spatial and temporal dependence can make ordinary random validation optimistic for genuinely independent predictions (Roberts et al., 2017; Valavi et al., 2019). Our framework applies that logic directly to multidimensional state organization. The comparator is deliberately the model's own marginal `P(A)`: the question is whether retaining the proposed conditioning structure earns predictive information beyond the lower-dimensional representation.

## 4.2 Independent transferability adds a stronger ecological claim

The Snapshot Serengeti result provides the complementary positive case. Temporal support within sites was broad, species identity partitioned detected time beyond a within-site permutation null, and species-conditioned temporal distributions outperformed the species-blind marginal in every held-out site fold. The framework therefore does not function only as a cautionary filter that rejects rich ecological patterns. It can also identify an empirical state in which organization survives a prospectively independent answer check.

This positive result matters because it makes the distinction between thickness and transferability empirical rather than purely conceptual. The bat and Serengeti lanes differ in many biological and observation-process features, so their numerical information values cannot be treated as controlled effect sizes and their contrast does not show that temporal dimensions are intrinsically more stable or generalizable than vertical dimensions. What the pair demonstrates is the **existence of distinct inferential states**: substantial added-axis information can occur with failed transfer, and substantial added-axis information can also occur with consistently positive independent transfer.

The generalization claim itself remains bounded by the design. The Serengeti folds are spatial groups within one camera-trap programme. Positive gains in all three folds do not establish transfer across regions, seasons, sensor systems or independently assembled data sets. More generally, the replication unit used in a transferability test should match the intended target of inference. The grouped scoring API is therefore agnostic to whether groups are individuals, years, sites or instruments, but the biological scope of the conclusion is not agnostic to that choice.

## 4.3 Estimability should be allowed to remain a scientific outcome

The Tawaki lane illustrates a different failure mode. Its prospectively defined site-by-year vertical endpoint was not structurally estimable under the frozen observation architecture, and the analysis stopped before biological thickness was opened. This outcome may appear less satisfying than a positive or negative biological result, but it protects the estimand. Changing spatial grain, denominators, identity reconciliation or data source after discovering a coverage problem would answer a different question while retaining the appearance of a predeclared test.

We therefore treat **unavailable** as a first-class terminal state. This is analogous to distinguishing missing information from evidence of absence. The scientific result is not “no vertical structure”; it is that the stated vertical claim could not be supported by the available architecture without changing its prospective definition. Such fail-closed behaviour is especially important when complex public data sources make many alternative preprocessing paths technically possible.

## 4.4 The mathematics can travel across axes, but ecological meaning cannot

A strength of the framework is that the same estimands can be applied to different added dimensions. Height, depth, time, season, behavioural state or structural habitat state can all be represented as declared axes in a support tensor. Conditional entropy, mutual information and conditional-versus-marginal log gain do not need a taxon-specific derivation for each application.

The biological interpretation, however, remains inseparable from measurement semantics. In the bat analysis, native GPS height above mean sea level was retained as such; it was not relabelled as height above ground. In the Serengeti analysis, source-reported Tanzania local clock time was retained; it was not converted post hoc to solar time and camera detections were not equated automatically with a complete activity distribution. These distinctions prevent mathematical portability from becoming semantic overreach.

Observation processes can also remain imperfect after explicit effort weighting. Camera detectability may vary with time, species and behaviour, and GPS error or terrain context can influence apparent vertical distributions. The framework does not solve those observation problems by itself. Instead, it makes them visible in the meaning assigned to the support tensor and in the ceiling placed on the resulting claim.

## 4.5 Cross-system differences demonstrate states, not mechanisms

It would be tempting to interpret the positive temporal result and negative vertical transfer as evidence for a biological contrast between temporal and vertical niche organization. The current design cannot support that interpretation. The two systems differ in taxon, movement scale, sensor technology, base axes, added-axis discretization, sample size, weighting and replication architecture. Their information values are therefore not commensurable estimates of one controlled biological effect.

The empirical comparison serves a narrower methodological role: it demonstrates that different terminal states predicted by the inferential hierarchy can occur in real data. Explaining why a system is thick but non-generalizing, or thick and generalizing, is a separate ecological question that would require a design controlling the relevant biological and observation-process differences. This separation prevents the demonstration data sets from being overburdened with a mechanistic claim they were not selected to test.

## 4.6 Projection-aware inference should end before downstream state promotion

The hierarchy developed here also clarifies a boundary that matters for downstream ecological workflows. A positive terminal summary is not automatically an axis-resolved state object suitable for propagation into a different model or decision system. For example, the Serengeti result establishes generalizing species-conditioned temporal organization under the frozen site-fold design, but the terminal receipt is a summary of evidence, not an integrity-pinned species-by-site-by-time state artifact intended for downstream reachability or survey optimization.

Keeping this boundary explicit prevents a common form of inferential drift: a statistic supporting a claim about organization becomes, through serialization or reuse, a new data product with stronger semantics than the original test justified. In the broader programme motivating this work, downstream state propagation is therefore treated as a separate interface requiring its own provenance and representation rules.

More generally, ecological maps should not be treated as thin merely because additional dimensions can be imagined, nor should multidimensional models be treated as validated merely because they fit. The evidence can be organized more usefully as a sequence: **Can the added axis be estimated? How much state survives projection? Is that state organized? Does the organization transfer independently?** The three empirical applications here show that each step can change the scientific conclusion. Projection loss is therefore not one property but an inferential problem with separable components, and generalizable multidimensional structure should be claimed only when the relevant components have each been demonstrated.

# Acknowledgements

[Omitted from anonymized review draft. Complete on title page after authorship and funding details are finalized.]

# Author contributions

[Omitted from anonymized review draft. Complete using CRediT roles in the non-anonymous title page.]

# Conflict of interest

[To be completed before submission.]

# References

Blonder, B., Lamanna, C., Violle, C. & Enquist, B. J. (2014). The n-dimensional hypervolume. *Global Ecology and Biogeography*. https://doi.org/10.1111/geb.12146

Cover, T. M. & Thomas, J. A. (2006). *Elements of Information Theory* (2nd ed.). Wiley.

Hutchinson, G. E. (1957). Concluding remarks. *Cold Spring Harbor Symposia on Quantitative Biology*, 22, 415–427. https://doi.org/10.1101/SQB.1957.022.01.039

Matsui, T. (2026). Assessing the transferability of species distribution models: A cross-continental evaluation. *Ecology and Evolution*, 16, e73534. https://doi.org/10.1002/ece3.73534

O'Mara, M. T., Amorim, F., Scacco, M., McCracken, G. F., Safi, K., Mata, V., Tomé, R., Swartz, S., Wikelski, M., Beja, P. et al. (2021). Bats use topography and nocturnal updrafts to fly high and fast. *Current Biology*, 31, 1311–1316. https://doi.org/10.1016/j.cub.2020.12.042. Data: Movebank Data Repository, https://doi.org/10.5441/001/1.52nn82r9

Otis, M., Mattern, T. & colleagues. (2025). Inter-colony and inter-annual behavioural plasticity in the foraging strategies of a fjord-dwelling penguin—good news in the face of environmental change? *PeerJ*, 13, e19650. https://doi.org/10.7717/peerj.19650. Data: https://doi.org/10.5281/zenodo.14849008

Roberts, D. R., Bahn, V., Ciuti, S., Boyce, M. S., Elith, J., Guillera-Arroita, G., Hauenstein, S., Lahoz-Monfort, J. J., Schröder, B., Thuiller, W. et al. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography*, 40, 913–929. https://doi.org/10.1111/ecog.02881

Sequeira, A. M. M. et al. (2018). Transferring biodiversity models for conservation: Opportunities and challenges. *Methods in Ecology and Evolution*. https://doi.org/10.1111/2041-210X.12998

Shannon, C. E. (1948). A mathematical theory of communication. *Bell System Technical Journal*, 27, 379–423, 623–656.

Swanson, A., Kosmala, M., Lintott, C., Simpson, R., Smith, A. & Packer, C. (2015). Snapshot Serengeti, high-frequency annotated camera trap images of 40 mammalian species in an African savanna. *Scientific Data*, 2, 150026. https://doi.org/10.1038/sdata.2015.26. Data: https://doi.org/10.5061/dryad.5pt92

Valavi, R., Elith, J., Lahoz-Monfort, J. J. & Guillera-Arroita, G. (2019). blockCV: An R package for generating spatially or environmentally separated folds for k-fold cross-validation of species distribution models. *Methods in Ecology and Evolution*. https://doi.org/10.1111/2041-210X.13107

Wenger, S. J. & Olden, J. D. (2012). Assessing transferability of ecological models: An underappreciated aspect of statistical validation. *Methods in Ecology and Evolution*. https://doi.org/10.1111/j.2041-210X.2011.00170.x

Yates, K. L. et al. (2018). Outstanding challenges in the transferability of ecological models. *Trends in Ecology & Evolution*, 33, 790–802. https://doi.org/10.1016/j.tree.2018.08.001
