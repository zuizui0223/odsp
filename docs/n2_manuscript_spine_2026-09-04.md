# N2 manuscript spine — paragraph-level draft map

Working title: **Beyond flat niche maps: separating added-axis thickness from transferable ecological organization**

Primary target: **Methods in Ecology and Evolution — Research Article**.

This file fixes paragraph purpose and evidence placement before prose expansion. It is intentionally stricter than a loose outline: each paragraph has one job, one evidence class and an explicit claim ceiling.

## 1. Introduction

### Paragraph 1 — the projection problem

Start from the Hutchinsonian idea that ecological niches are multidimensional. Modern mapping, monitoring and species-distribution workflows nevertheless collapse ecological support into lower-dimensional products, most often horizontal maps. The problem is not that maps are wrong; it is that marginal projection can hide state structure along vertical, temporal or other axes.

Cite: Hutchinson 1957; Blonder et al. 2014.

End with: **a fitted multidimensional representation does not by itself tell us what inferential status the hidden state has.**

### Paragraph 2 — the inferential gap

Separate four questions that are often bundled together:

1. can the added axis be estimated under the declared observation architecture?
2. how much state information remains after the retained/base state is known?
3. is that state systematically organized?
4. does the organization improve prediction in independent data relative to the lower-information marginal representation?

This is the paper's novelty statement. Do not claim that previous niche or transferability literature is missing; claim that these layers are not normally combined into one explicit fail-closed hierarchy for multidimensional ecological support.

### Paragraph 3 — why transferability changes the claim

Ecological models can fit well yet fail when transferred across space, time or other independent replication units. Random validation can also understate error when dependence is ignored. Therefore, descriptive multidimensional geometry must be separated from independent transferability.

Cite: Wenger & Olden 2012; Roberts et al. 2017; Valavi et al. 2019; Yates et al. 2018; Sequeira et al. 2018; Matsui 2026.

End with: **the appropriate comparator is not “did the multidimensional model fit?”, but “did conditioning on the added structure improve held-out prediction over the lower-information marginal?”**

### Paragraph 4 — what ODSP contributes

Introduce the method in one compact chain:

`estimability -> thickness -> organization -> independent transferability`.

Define the two main numerical ideas without equations yet:

- conditional entropy/effective states for thickness;
- conditional-versus-marginal held-out log-score gain for transferability.

State that independent groups are scored separately, with cross-fitting when appropriate.

### Paragraph 5 — validation and empirical design

State the testing strategy before giving results:

- analytic known-truth families;
- concealed finite-observation recovery;
- three prospectively bounded empirical lanes chosen to expose different observation architectures and added-axis semantics.

Predictions:

- thick but unorganized known truth should have positive thickness but zero organization/gain;
- stable organization should have positive fitted information and positive held-out gain;
- shifted organization should retain fitted information but yield negative held-out gain;
- empirical lanes may legitimately terminate as unavailable, non-generalizing or generalizing.

## 2. Materials and Methods

### 2.1 State representation and projection

Let `B` denote the retained/base axes and `A` the added ecological state axes. A non-negative support array is normalized to a probability distribution only for the declared analysis. Define:

- `H(A|B)` as added-axis information after base state is known;
- `exp(H(A|B))` as the number of effective added states.

Clarify that support semantics are explicit: species use/support and structural capacity are different objects.

### 2.2 Fitted organization

Use mutual information only for in-sample organization:

- generic `I(A;B)`;
- conditional `I(C;T|B)` for identity partitioning of time within context.

State plainly: **organization is not transferability**.

### 2.3 Held-out conditional-versus-marginal transferability

Define the score:

`G = E_heldout[log P_model(A|B) - log P_model(A)]`.

Interpretation:

- `G > 0`: conditioned structure improves held-out prediction over the model marginal;
- `G <= 0`: it does not.

No hidden smoothing is introduced by the generic core. Any pseudocount or smoothing rule must be specified prospectively by the empirical design.

### 2.4 Independent groups and cross-fitting

Each independent individual, year, site fold or instrument receives one gain. Group mass is not pooled into the terminal decision.

At zero tolerance:

- every gain > 0 -> `generalizing`;
- every gain <= 0 -> `non_generalizing`;
- otherwise -> `mixed`.

For cross-fitted designs, each held-out group is scored against a model trained without that group.

### 2.5 Known-truth benchmark

Report the analytic families first, following MEE's expectation that a computational method be demonstrated under known truth.

Core families:

1. **Thick-unorganized**: 4 effective added states, `I(A;B)=0`, held-out gain `0`.
2. **Stable organization**: fitted information = held-out gain = `0.13081203594113697` nats.
3. **Shifted organization**: fitted information remains `0.13081203594113697` nats, but held-out gain = `-0.41849410839291784` nats.

Also summarize projection-loss fixtures where identical horizontal marginals conceal disjoint vertical, temporal or joint states.

### 2.6 Source and axis semantics

Describe the source-preserving temporal and vertical information rules:

- do not substitute upload time for biological observation time;
- do not turn date-only records into midnight observations;
- do not relabel locality elevation or sensor placement as organism vertical state;
- retain uncertainty/missingness rather than inventing an axis value.

### 2.7 Prospectively frozen empirical lanes

Keep this concise in the main text; move detailed contract histories to Supporting Information.

#### Tawaki

Purpose: test whether the empirical vertical endpoint is structurally estimable under the predeclared site×year architecture.

Terminal rule: structural failure ends the lane before biological thickness is opened.

#### European free-tailed bat

Added axis: native GPS `height_above_msl`.

Base: 5-km horizontal cells.

Replication: 6 model individuals / 2 sealed individuals, individual-equal weighting.

Primary question: does `P_model(z|x,y)` outperform `P_model(z)` in each sealed bat?

#### Snapshot Serengeti

Added axis: six fixed four-hour source-local-clock time states.

Context: camera site.

Identity: admitted mammal species.

Effort: inverse valid camera-days.

Partition test: 199 within-site species-label permutations.

Transfer: three deterministic held-out site folds, each with its own leave-one-fold-out model.

## 3. Results

### 3.1 Known truth separates thickness from organization and transferability

Report the three analytic transferability families in one paragraph and one figure.

Essential result sentence:

> The same fitted thickness can coexist with zero, positive or negative held-out gain depending on whether added-state organization is absent, stable or shifted.

This is the mathematical result that makes the empirical interpretation possible.

### 3.2 Estimability is an empirical outcome

Tawaki terminated at `empirical_gate_d_unavailable` because the frozen full site×year structural denominator was not recoverable. No biological `H(Z|X,Y)` was opened.

Essential interpretation:

> This is not evidence of absent vertical niche structure; it is evidence that the predeclared empirical claim was not estimable from the available observation architecture.

### 3.3 Bat support is vertically thick

Report:

- 10,335 / 10,335 finite native heights;
- 18 frozen eligible 5-km cells;
- `H(Z|X,Y)=1.3918623004770097` nats;
- effective vertical states `4.022333876564191`.

Essential interpretation:

> Horizontal projection removes substantial descriptive vertical-state information from the model-pool support.

### 3.4 Bat vertical organization does not transfer

Report sealed gains:

- Bat5 `-0.43541033813280833`;
- Bat7 `-0.021938657402345435`.

Both are non-positive, so terminal category is `empirical_n2_thickness_not_generalizing`.

Essential result sentence:

> Descriptive thickness was therefore present without independent support for its detailed x-y-conditioned organization.

### 3.5 Serengeti time is thick and species-partitioned within sites

Report:

- 17 species passed outcome-blind admission;
- `H(T|Site)=1.6396235816361795` nats;
- effective temporal states `5.153229376935854` of six;
- `I(Species;T|Site)=0.22427598739601606` nats;
- permutation `p=0.005`.

Do not call this causal temporal displacement.

### 3.6 Serengeti temporal organization transfers across independent site folds

Report gains:

- `0.0572411993741857`;
- `0.045158861333215006`;
- `0.04514355468571751`.

All are positive, so terminal category is `temporal_partition_generalizing`.

Essential result sentence:

> Species-conditioned detected-time organization improved prediction over the species-blind temporal marginal in every prospectively held-out spatial fold.

### 3.7 Three empirical terminal states expose the inferential hierarchy

Use the state matrix rather than treating the three systems as a biological comparison.

- Tawaki: unavailable;
- bat: thick / non-generalizing;
- Serengeti: thick / generalizing.

Chapter-level result:

> Projection loss has at least two empirically separable components: the amount of added-axis state retained after projection and the independent transferability of the organization of that state.

## 4. Discussion

### 4.1 Multidimensional geometry is descriptive until independently tested

Lead with the bat result. It provides the strongest reason the method is needed: a large conditional entropy cannot be promoted automatically into generalizable multidimensional ecological structure.

Connect to hypervolume literature without criticizing it for answering a different question.

### 4.2 Independent transferability adds a stronger claim

Use Serengeti as the positive counterexample. The framework does not merely reject rich models; it can identify a state where organization survives independent transfer.

Connect to ecological model-transfer literature and blocked validation.

### 4.3 Unavailability should not be repaired after outcome access

Use Tawaki to argue for explicit estimability gates. A fail-closed unavailable endpoint is scientifically cleaner than silently changing spatial grain, state bins or dataset after seeing a problem.

### 4.4 The framework is axis-agnostic but interpretation is not

The same mathematics can treat height, depth, time or structural states. Biological meaning remains tied to measurement semantics.

Explicit limitations:

- native altitude is not height above ground;
- camera-detected source clock time is not necessarily activity time or solar time.

### 4.5 Cross-system contrasts demonstrate states, not mechanisms

Do not infer that temporal organization is intrinsically more stable than vertical organization. Bat and Serengeti differ in taxa, sensors, base axes, sampling and data-generating processes.

The contrast proves that the inferential states exist empirically, not why one system occupies one state.

### 4.6 Projection-aware inference should end before downstream state promotion

Close by maintaining the N2/N3 boundary. A terminal summary can justify an inferential statement without constituting the axis-resolved state artifact needed for downstream reachability or survey planning.

## Main displays

### Figure 1 — Inferential hierarchy

Panels:

A. multidimensional support `S(B,A)` and projection to `S(B)`;
B. `H(A|B)` / effective-state thickness;
C. fitted organization;
D. independent conditional-versus-marginal held-out gain and terminal classification.

### Figure 2 — Known-truth validation

Show three matched schematic families:

- thick/unorganized: 4 states, `I=0`, gain `0`;
- stable: `I=0.1308`, gain `+0.1308`;
- shifted: `I=0.1308`, gain `-0.4185`.

### Figure 3 — Empirical state matrix

Left: Tawaki unavailable.

Center: bat `H=1.392`, 4.02 states, two negative gains.

Right: Serengeti `H=1.640`, 5.15 states, `I=0.224`, `p=0.005`, three positive gains.

Bottom strip: unavailable -> thick/non-generalizing -> thick/generalizing.

### Table 1 — Estimands and claim ceilings

Columns:

- inferential layer;
- quantity;
- null/comparator;
- replication unit;
- positive interpretation;
- prohibited interpretation.

## Supporting Information

Keep the main paper conceptually lean. Put the following in supplements:

- complete prospective contract timeline;
- source-preflight details;
- frozen sensitivity results;
- recovery/serialization audit trail for the Serengeti workflow;
- full local-cell bat thickness table;
- extra known-truth fixtures;
- payload/handoff schema details.

The technical recovery history is important for auditability but should not dominate the biological/methodological narrative in the main text.
