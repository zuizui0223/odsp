# Binary error probability bounds implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task. Track progress with the checkboxes below.

**Goal:** Add a reproducible aggregate-only bound on erroneous true-class
probabilities and severe-error counts, with a twelve-cell Swiss application.

**Architecture:** A standard-library script validates pinned inputs, reuses the
previous proper-score audit, recovers integer accuracy counts and computes
conservative Decimal bounds. A synthetic test suite and a dedicated workflow
verify the arithmetic and evidence boundary.

**Tech Stack:** Python >=3.10, standard library decimal, pytest >=8,<10.

**Spec:** `docs/superpowers/specs/2026-11-22-binary-error-probability-bounds-design.md`

## Global constraints

- All twelve 2020/2021/2022 x HR/nest x full/purged cells; eight seeds per cell.
- No source RDS, GPS, individual labels, IDs, probabilities or forest refits.
- Rounding radius 0.000001000001; conservative probability floor 0.000000999999;
  severe-error threshold 0.01, chosen after observing the existing anomaly.
- Conditional quantities are null for zero errors. Counts refer to seed-record
  predictions. No confidence interval, p-value, new ecological mechanism or
  future-animal coverage claim.
- Preserve original contract/receipt bytes and all historical terminal states.

## Review focus

1. An integer-boundary ceiling must not invent an extra severe error; test a
   known four-record example with exactly one probability below 0.01.
2. A rounded accuracy that admits zero or multiple integer counts must fail;
   test an off-lattice value and an explicitly broad uncertainty interval.
3. Accuracy one must not produce a conditional bound or an existence claim;
   test feasible all-correct and impossible excessive-loss inputs.
4. A wrong rounding endpoint can strengthen a bound; test known prediction
   arrays after the source's two rounding stages and outward serialization.
5. Output aliases can destroy pinned evidence; test direct, relative, symlink
   and hardlink aliases of every protected input, plus ordinary file/stdout.

## Task 1: Mathematical diagnostic and pinned replay

**Files:** create `research/BOP_SWISS_ERROR_PROBABILITY_BOUNDS_V1_CONTRACT.json`,
`scripts/bop_swiss_error_probability_bounds_v1.py` and
`tests/test_bop_swiss_error_probability_bounds_v1.py`.

**Consumes:** `load_locked()` and `analyze()` from the pinned PR #300 script;
the source receipt's twelve means and fixed cohort/seed counts.

**Produces:** `binary_error_bounds(...) -> dict`, `replay() -> dict`,
`protected_paths() -> tuple[Path, ...]`, and the module CLI.

- [ ] Commit this design, plan and the exploratory replay contract before code.
- [ ] Write synthetic tests first. For A=.5 and L=ln(4), N=2, the error
      probability upper bound must enclose .125; for the low-loss tie example
      (.8,.5), it must enclose .5. All-correct must return null bounds.
- [ ] Run the new tests and observe a missing-implementation failure.
- [ ] Implement the checked Decimal inequalities and uniquely recovered counts.
- [ ] Add the all-twelve replay, source/claim drift, known-array, impossible-
      input, protected-output and normal-output tests; observe missing behavior
      failures before implementing those parts.
- [ ] Run new and previous proper-score suites; require all cases to pass.

## Task 2: Reproducible result and integration

**Files:** create `.github/workflows/bop-swiss-error-probability-bounds-v1.yml`,
`docs/bop_swiss_error_probability_bounds_v1.md`; update README and manuscript
`BOP_INDEPENDENT_ANIMAL_GAIN_METHODS_DRAFT_v1.md` with a new section 3.14.

**Consumes:** Task 1's successful all-twelve report; exact protected source blobs.
**Produces:** the twelve-cell table, derivation and documented evidence limits.

- [ ] Run the module to a temporary aggregate-only JSON and use its actual
      values in the report. No new source inputs or performance metric choices.
- [ ] Add matrix CI running both diagnostic suites and replaying all twelve
      cells. Check output/inputs, without fetching biological source data.
- [ ] Obtain independent whole-branch review; fix substantive issues and verify.
- [ ] Create the PR, wait for current-head common and dedicated CI, and integrate
      the reviewed tree. Verify the merged tree matches the tested tree.

## Execution record

- Base main: `13b884f5cfb94beef36e8e5c5b031559e81b8b4b`.
- The mathematical formula and source metric semantics were independently
  reviewed before implementation. Two-stage rounding and 256 pooled predictions
  in 2022 were verified from the frozen R source and aggregate receipt.
- The working snapshot contains selected code/aggregate files only; GitHub
  branch isolation supplies the repository history without fetching biological
  source data. Implementation and final review proceed without a new permission
  round under the user's standing action-first instruction.
