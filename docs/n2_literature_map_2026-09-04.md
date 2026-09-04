# N2 literature map — manuscript framing

This is a **framing map**, not a completed systematic review. It identifies the minimum literature spine needed to position the N2 method without inflating the bibliography before the full manuscript is drafted.

## 1. Multidimensional niche as the starting concept

### Hutchinson 1957

G. E. Hutchinson. *Concluding Remarks*. Cold Spring Harbor Symposia on Quantitative Biology 22:415–427. https://doi.org/10.1101/SQB.1957.022.01.039

Use for:

- the n-dimensional niche/hypervolume foundation;
- the point that an ecological niche is conceptually multidimensional before any mapping or projection step.

Do **not** use Hutchinson to imply that every observed state tensor is a fundamental niche. ODSP empirical tensors remain observation- and support-defined.

### Blonder et al. 2014

Benjamin Blonder et al. *The n-dimensional hypervolume*. Global Ecology and Biogeography. https://doi.org/10.1111/geb.12146

Use for:

- modern computational treatment of high-dimensional ecological hypervolumes;
- precedent that geometry in multiple dimensions is an explicit methodological object;
- contrast with ODSP: hypervolume geometry asks what the fitted multidimensional state space looks like, while ODSP additionally asks how much information is lost by projection and whether detailed organization transfers independently.

## 2. Transferability is not ordinary fit

### Wenger & Olden 2012

Seth J. Wenger & Julian D. Olden. *Assessing transferability of ecological models: an underappreciated aspect of statistical validation*. Methods in Ecology and Evolution. https://doi.org/10.1111/j.2041-210X.2011.00170.x

Use for:

- the conceptual separation between predictive accuracy in a reference setting and model generality/transferability;
- historical precedent in the target journal itself;
- motivation for treating transferability as an additional claim rather than a synonym for fitted organization.

### Roberts et al. 2017

David R. Roberts et al. *Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure*. Ecography 40:913–929. https://doi.org/10.1111/ecog.02881

Use for:

- why random cross-validation can underestimate predictive error when dependence structures exist;
- justification for deliberately independent or blocked replication units;
- support for the Serengeti site-fold design and the broader rule that answer checks should reflect the intended transfer target.

### Valavi et al. 2019

Roozbeh Valavi et al. *blockCV: An R package for generating spatially or environmentally separated folds for k-fold cross-validation of species distribution models*. Methods in Ecology and Evolution. https://doi.org/10.1111/2041-210X.13107

Use for:

- implementation precedent for spatial/environmental independence in ecological validation;
- practical context for why ODSP scores prospectively independent groups separately rather than pooling their mass.

## 3. Transferability remains an open ecological problem

### Yates et al. 2018

Katherine L. Yates et al. *Outstanding Challenges in the Transferability of Ecological Models*. Trends in Ecology & Evolution 33:790–802. https://doi.org/10.1016/j.tree.2018.08.001

Use for:

- broad evidence that transferability is a major unresolved ecological modelling issue;
- the identified need for widely applicable transferability metrics;
- motivation for an axis-agnostic conditional-versus-marginal score.

### Sequeira et al. 2018

Ana M. M. Sequeira et al. *Transferring biodiversity models for conservation: Opportunities and challenges*. Methods in Ecology and Evolution. https://doi.org/10.1111/2041-210X.12998

Use for:

- transparent definitions of reference and target systems;
- precedent for reporting assumptions and transfer conditions explicitly;
- connection to the MEE readership.

### Matsui 2026

Takayuki Matsui. *Assessing the Transferability of Species Distribution Models: A Cross-Continental Evaluation*. Ecology and Evolution 16:e73534. https://doi.org/10.1002/ece3.73534

Use for:

- current evidence that conventional random holdout validation can rate models favorably while performance in independent target regions differs strongly;
- contemporary motivation for independent answer checks.

This is a supporting recent reference, not the conceptual origin of ODSP.

## 4. Information theory

### Shannon 1948

Claude E. Shannon. *A Mathematical Theory of Communication*. Bell System Technical Journal 27:379–423, 623–656.

Use for:

- Shannon entropy as the mathematical basis of state information;
- conditional entropy and mutual information definitions.

### Cover & Thomas

Thomas M. Cover & Joy A. Thomas. *Elements of Information Theory*.

Use for:

- conditional entropy, mutual information and expected log-likelihood-ratio identities;
- formal explanation of why, under the same generating distribution, expected conditional-versus-marginal log gain corresponds to information supplied by the conditioning state.

The manuscript should not spend space re-deriving standard information theory beyond what is needed to define the estimands.

## 5. The gap ODSP should claim

The manuscript should **not** claim that ecology lacks multidimensional niche methods or lacks transferability methods. Both literatures are mature.

The narrower gap is:

> Multidimensional ecological geometry and model transferability are usually treated as separate methodological problems. A fitted multidimensional representation can therefore be interpreted as biologically rich without an explicit inferential hierarchy that distinguishes (i) whether the added axis is estimable, (ii) how much state information survives projection, (iii) whether that state is organized, and (iv) whether the organization improves prediction in prospectively independent data relative to the lower-information marginal representation.

That is the defensible novelty claim.

## 6. References to add during full drafting

Before submission, expand selectively in four directions:

1. ecological niche / hypervolume methods after Blonder 2014;
2. standards and diagnostics for species-distribution/ecological-niche models;
3. proper scoring rules and log-score interpretation where needed;
4. vertical and temporal niche applications that demonstrate why added-axis semantics matter biologically.

Do not turn the Introduction into a comprehensive history of niche theory. The MEE paper should remain a methods paper centered on the inferential gap.
