# Group-gain population-content implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task. Track progress with the checkboxes below.

**Goal:** Correct the rank-to-population overclaim and make a distinct exact
positive-content test executable on predeclared independent animal gains.

**Architecture:** One additive module binds a content policy to an existing
fixed forecast plan, performs a count-only gate, reuses existing calibration
scoring, and applies an exact rational binomial decision. Historical rank and
scoring modules are unchanged.

**Tech Stack:** Python >=3.10, standard library Fraction/math/dataclasses,
existing NumPy-backed package, pytest; no new runtime dependencies.

**Spec:** `docs/superpowers/specs/2026-11-22-group-gain-content-design.md`.

## Global constraints

- One selected stratum and one pre-outcome fixed threshold/content/confidence.
- Required sampling declaration: `iid_group_gains_within_prespecified_stratum`.
- Fixed sample size; no outcome-driven stopping, post hoc stratum selection,
  simultaneous-stratum claim or automatic conditioning on feature rosters.
- Use calibration labels only; preserve a reserved validation group and reuse
  `FrozenGainCalibration` in the existing untouched-validation function.
- Do not change legacy rank outputs, source contracts, receipts or scientific
  terminals; no biological outcome access and no forest refits.

## Review focus

1. Treating marginal rank coverage as a conditional population guarantee.
2. Reversing a binomial tail or counting ties as successes.
3. Using binary float rounding to decide an exact probability boundary.
4. Pooling strata or scoring labels despite an insufficient-count preflight.
5. Accepting changed policies/artifacts or consuming validation labels.

## Task 1: Frozen exact-content API and tests

**Files:** create `odsp/group_gain_content.py` and
`tests/test_group_gain_content.py`.

**Consumes:** `FrozenGroupForecastPlan.assert_unchanged`,
`calibrate_fixed_group_gain` and its `FrozenGainCalibration` result.
**Produces:** `FrozenGroupGainContentPlan`, `GroupGainContentAssessment`,
`freeze_group_gain_content_plan(...)`, `assess_group_gain_content(...)`.

- [x] Write tests first: nine positive gains can have a positive rank bound but
      fail the content count gate; 28 all-positive fail / 29 pass at .9/.95;
      45 with one nonpositive fail / 46 pass; equality with threshold fails.
- [x] Run tests and observe the missing implementation failure.
- [x] Implement validated policy freezing, exact rational tail evaluation,
      conservative display and calibration-only evaluation with legacy reuse.
- [x] Add exact-boundary, stratum, poisoned-outcome count-HOLD, malformed input,
      changed policy/plan/artifact and wrong-role cases; verify real behavior.
- [x] Run new tests plus existing rank, fixed-protocol and managed-forecast tests.
- [x] Review code and commit the verified additive implementation.

## Task 2: Correct interpretation and integrate

**Files:** modify `docs/bop_individual_gain_inference_theory_v1.md`,
`docs/bop_method_spine_v1.md`, `README.md`,
`manuscript/BOP_INDEPENDENT_ANIMAL_GAIN_METHODS_DRAFT_v1.md`;
create `docs/bop_group_gain_content_v1.md` and
`.github/workflows/bop-group-gain-content-v1.yml`.

**Consumes:** Task 1 API and verified exact known-count calculations.
**Produces:** Correct joint-event interpretation, counterexample, operational
9-versus-29 distinction, API example and scoped automated validation.

- [x] Replace the invalid implication with the joint-event bound and explicit
      calibration-selection caveat; retain the original correct rank lemma.
- [x] Document IID/fixed-sample requirements, strict threshold, one-stratum
      scope, frequentist interpretation and unchanged biological conclusions.
- [x] Add matrix CI for the new API and its existing upstream protocols.
- [ ] Obtain independent whole-change review and resolve substantive findings.
- [ ] Require current-head dedicated/common CI, merge, and verify tree identity.

## Execution record

- Base main: `76c3ec80a21c0277351a5f7e53baa36a7e150ce4` (PR #302 merged).
- Root and an independent mathematical reviewer confirmed the counterexample,
  joint-event correction and 28/29, 45/46 exact binomial boundaries before code.
- Existing local rank/fixed/managed protocol tests pass (60 collected cases).
- The checkout is a selected, hash-verified repository snapshot. GitHub branch
  isolation supplies history; no source biological records are materialized.
- The user has instructed autonomous execution, including routine review/merge;
  design choices are recorded here without another permission round.

- Task 1 complete: new tests first stopped for the absent module. The additive
  implementation and 53 new cases now pass alongside 60 legacy cases (113).
  Exact binomial recurrence matched direct combinatorial expansion and SciPy
  one-sided binomtest on 816 cases. Replacing only the decision with binary
  float arithmetic made the strict rational-boundary test fail; a fresh
  unmodified process passed all 113 cases.
- The overflow rejection test initially required a particular error message;
  the upstream calibrator already rejects nonfinite scores while hashing.
  The test now checks rejection itself, not wording. No production workaround
  or legacy scoring modification was needed.
- Pre-flight interface: Task 2 documents the actual policy/assessment methods
  implemented by Task 1; calibration output is the unchanged legacy type.
- Task 2 documentation and CI are implemented. The complete synthetic example
  executes successfully, including a positive content decision followed by a
  negative reserved validation gain. A fresh focused run passes 113 cases;
  byte comparison confirms the existing rank, fixed-forecast, managed-forecast
  and package-initialization modules are unchanged. The PR integration record
  will retain independent review, exact-head CI and post-merge tree evidence.
