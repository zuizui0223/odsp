# N2 submission plan — 2026-09-04

## Decision

Primary target: **Methods in Ecology and Evolution (MEE), Research Article**.

Current journal guidance was checked on 2026-09-04 against the official MEE aims/scope and author guidelines:

- https://besjournals.onlinelibrary.wiley.com/hub/journal/2041210x/aims-and-scope/read-full-aims-and-scope
- https://besjournals.onlinelibrary.wiley.com/hub/journal/2041210x/author-guidelines
- https://besjournals.onlinelibrary.wiley.com/hub/journal/2041210x/policyonpublishingcode.html

The fit is strongest when the paper is written as a **general inferential method** and the three empirical lanes are demonstrations of distinct terminal states, rather than as a comparative biological study of bats, penguins and Serengeti mammals.

MEE explicitly prioritizes new analytical, practical or conceptual methods over the biological results of applying them. Its Research Articles should be broadly applicable across taxa or systems and normally test computational methods using simulations or benchmark data before empirical applications. ODSP already has that architecture: analytic known-truth families and concealed finite-observation recovery precede the prospectively bounded empirical lanes.

## Submission sequence

### 1. Methods in Ecology and Evolution — first submission

Article type: **Research Article**.

Working title:

> **Beyond flat niche maps: separating added-axis thickness from transferable ecological organization**

Why this title works:

- it starts with the familiar problem (flat niche maps);
- it names the genuinely new distinction (thickness versus transferable organization);
- it does not overclaim a universal biological mechanism;
- it keeps the paper method-centered rather than taxon-centered.

Target length: **<=7,500 words total** to leave margin below the journal's 7,000–8,000-word ceiling, which includes references, captions and statements.

Recommended working budget before references/captions:

- Abstract: 280–330 words;
- Introduction: 800–950;
- Methods: 2,100–2,400;
- Results: 1,150–1,350;
- Discussion: 1,300–1,550;
- remaining allowance: references, captions, data/code statement and declarations.

The abstract must be numbered 1–4 and should not exceed 350 words.

### 2. Ecography — fallback

Official scope checked 2026-09-04:

- https://nsojournals.onlinelibrary.wiley.com/journal/16000587

Ecography explicitly welcomes work that advances understanding of ecological patterns through space and time using modern methodology. The paper could fit, but the framing would need to move from **method uptake** toward **what projection does to ecological inference across spatial and temporal dimensions**.

For an Ecography resubmission, retain the same analyses but change emphasis:

- lead with ecological projection through space/time rather than software/method validation;
- move the empirical state matrix earlier;
- describe the known-truth benchmark as validation of a conceptual framework rather than the main contribution;
- strengthen connections to ecological niche and biogeographical mapping literature.

### 3. Global Ecology and Biogeography — lower-priority fallback

Official scope checked 2026-09-04:

- https://onlinelibrary.wiley.com/page/journal/14668238/homepage/productinformation.html

The journal accepts methodological studies that produce globally relevant conceptual conclusions, but it strongly emphasizes broad spatial, temporal or taxonomic patterns. The current three-lane evidence is better suited to MEE than to a macroecological journal because the paper demonstrates **possible inferential states**, not their broad-scale frequency across many taxa.

## Paper identity

This is **not** a paper whose central claim is that niches have three or four dimensions.

The paper asks a stricter question:

> When a multidimensional ecological support distribution is projected onto a lower-dimensional map, what evidence is required before the lost state structure can be called biologically informative and independently generalizable?

The answer is an inferential hierarchy:

1. **Estimability** — can the added axis be estimated under the prospectively frozen observation architecture?
2. **Thickness** — how much added-axis state remains after the base state is known?
3. **Organization** — is added-axis state systematically structured with respect to the declared base or identity axes?
4. **Transferability** — does that organization improve prediction in prospectively independent support compared with the lower-information marginal representation?

The empirical programme then occupies three different terminal states:

- Tawaki: unavailable at the estimability gate;
- European free-tailed bat: thick but non-generalizing;
- Snapshot Serengeti: thick, partitioned and generalizing.

## Methods order for MEE

MEE guidance favors method validation before empirical application. The manuscript should therefore use this order.

### 2.1 State representation and projection

Define a non-negative support tensor `S(B,A)` where `B` is the declared retained/base state and `A` is an added ecological axis or axis set.

Primary descriptive quantity:

`H(A|B)` and `exp(H(A|B))`.

State clearly that this is conditional state information, not occupancy probability, causal interaction strength or fundamental-niche volume.

### 2.2 Organization and held-out transferability

Keep fitted organization and generalization separate.

Fitted organization examples:

- `I(A;B)`;
- `I(C;T|B)` when identity `C` partitions time within context `B`.

Held-out answer check:

`E_heldout[log P_model(A|B) - log P_model(A)]`.

The marginal `P_model(A)` is the explicit lower-information comparator.

### 2.3 Independent groups and cross-fitting

Explain that replication units are scored separately. A large group cannot rescue an independent group with conflicting gain. Generalizing requires every predeclared independent gain to exceed the frozen tolerance.

For cross-fitted designs, each held-out group can have its own model trained without that group.

### 2.4 Known-truth validation

Lead with the analytic families:

1. thick but unorganized;
2. stable organization with positive held-out gain;
3. shifted organization with negative held-out gain despite positive fitted organization.

Then include concealed finite-observation recovery as the practical benchmark.

### 2.5 Observation semantics and prospective empirical gates

Explain why vertical/time fields cannot be manufactured from locality elevation, upload time or other convenient metadata. Describe the prospective contracts and the rule that unavailable or negative endpoints are terminal rather than triggers for tuning.

### 2.6 Empirical lanes

Keep dataset-specific details concise in the main text and move long preflight inventories to Supporting Information.

## Results order

### 3.1 Known truth recovers the intended inferential states

The method must first show it can distinguish thickness from organization and transferability under known generating processes.

### 3.2 A multidimensional question can be prospectively unestimable

Tawaki is not a biological null. It demonstrates that the observation architecture can fail before a biological thickness result is opened.

### 3.3 Vertical thickness can be substantial without transferable organization

European free-tailed bat:

- `H(Z|X,Y) = 1.3918623004770097` nats;
- `exp(H) = 4.022333876564191` effective vertical states;
- sealed gains `-0.43541033813280833`, `-0.021938657402345435`.

Interpretation: substantial descriptive vertical thickness, but no independent support for the detailed `P(z|x,y)` organization.

### 3.4 Temporal organization can generalize independently

Snapshot Serengeti:

- 17 admitted species;
- `H(T|Site) = 1.6396235816361795` nats;
- `exp(H) = 5.153229376935854` effective four-hour states out of six;
- `I(Species;T|Site) = 0.22427598739601606` nats;
- permutation `p = 0.005`;
- held-out site-fold gains `0.0572411993741857`, `0.045158861333215006`, `0.04514355468571751`.

Interpretation: camera-detected local-clock-time organization is both detected and independently generalizing across all three frozen spatial folds.

### 3.5 Projection loss has empirically separable inferential components

Use the state matrix as the chapter-level result. Do not compare the bat and Serengeti information values as controlled effect sizes.

## Discussion structure

### 4.1 A thick fitted niche is not enough

The bat result is the key negative demonstration. Conditional entropy can be substantial even when detailed organization fails every independent answer check.

### 4.2 Generalization is an additional ecological claim

The Serengeti result shows that positive independent transfer is possible under the same framework. This is what prevents the paper from becoming a purely cautionary critique.

### 4.3 Estimability belongs inside inference

Tawaki supports a general methodological point: observation architecture should be allowed to return unavailable rather than silently changing the target estimand.

### 4.4 Added-axis semantics matter

Time and vertical state are examples, not interchangeable quantities. The framework travels across axes because the estimands are abstract, while ecological interpretation remains axis-specific.

### 4.5 Limits of the empirical contrast

Do not infer that temporal niches are more stable than vertical niches. The systems differ in organism, sampling, conditioning variables and measurement process.

### 4.6 Chapter boundary

An N2 terminal summary, including a positive one, is not automatically an N3 state map. State artifacts require their own integrity-pinned representation.

## Display plan

For MEE, use three main figures rather than making the empirical synthesis the first figure.

**Figure 1 — Method hierarchy.** Projection from `S(B,A)` to the retained representation; estimability, thickness, organization and independent transferability; explicit marginal comparator.

**Figure 2 — Known-truth validation.** Three synthetic families: thick/unorganized, stable/generalizing and shifted/non-generalizing. This is essential for MEE because the paper's main output is a method.

**Figure 3 — Empirical terminal states.** Tawaki unavailable; bat thick/non-generalizing; Serengeti thick/generalizing. Reuse the validated values in `N2_CORE_FIGURE_SPEC.json` and `N2_EMPIRICAL_STATE_MATRIX.json`.

**Table 1 — Estimands and interpretation.** For each layer: quantity, comparator/null, replication unit, what a positive result means, and what it does not mean.

## Submission-readiness work still required

1. Create full English manuscript text under the MEE structure.
2. Curate the literature around niche projection, conditional entropy/information, ecological state spaces, transferability and out-of-sample validation.
3. Generate the three manuscript figures from machine-pinned specifications.
4. Prepare an anonymized code/data snapshot for double-anonymous review; do not point reviewers directly to an identifying public repository.
5. Add Data/Code for peer review statement directly below the abstract.
6. Prepare separate title page with authorship, affiliations, contributions, acknowledgements and data availability.
7. Check all third-party dataset licenses and citations in the final reference list.

A pre-submission enquiry is optional. It is worth using only after the numbered abstract and Figure 1 are stable enough to demonstrate that this is a broadly applicable method rather than a workflow tying together existing statistics.
