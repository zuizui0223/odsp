# Independent numerical verification of bat–fruit stratum CMI v2 (2026-11-23)

**Clearly post-original-output arithmetic verification**, not a new frozen hypothesis. The original source-open exploratory v1 [Actions #45081870409](https://github.com/zuizui0223/odsp/actions/runs/45081870409) established source-corrected layer counts `61/109/154`, 324 observed interactions, 9 bats, 37 plants, 89 pooled positive pairs. Registered source-count CMI: `I(Plant;capture layer|Bat)=0.2581875907325644`, within-bat margin-preserving null mean 0.2428811658 and p 0.200; `I(Bat;capture layer|Plant)=0.2449384764233592`, within-plant null mean 0.1722039187 and p 0.0005 (1999 permutations each, fixed seeds in v1).

This v2 independently:
1. Re-download *author original* four matrices at commit `3d4ede895b9c5c2b9419f94458e3badb7440d932`; verify the four Git blob SHA1, two-way 324-event sums and **every pooled bat×fruit cell**.
2. Use NumPy tensor entropy identities rather than import any v1 CMI or null helper:
   - `I(P;Z|B)=H(B,P)+H(B,Z)-H(B)-H(B,P,Z)`;
   - `I(B;Z|P)=H(B,P)+H(P,Z)-H(P)-H(B,P,Z)`.
   Verify exact 1e−10 agreement with original computed CMI. No biological parameter selected post-output.
3. As an **algorithmic sensitivity** only, repeat the within-bat and within-plant fixed-margin permutation null independently using NumPy's different RNG `default_rng(20261127)`, `default_rng(20261128)`, 1999 draws each, with the same source grouping margins. Unlike v1's deterministic RNG receipt, the exact p values are NOT required to match; report them and whether the qualitative original classifications at 5% remain: primary **not beyond null** and complementary **beyond null**. Do not change the original v1 results if this differs; investigate with a scientific audit.
4. No new ecological causal claim, independent site/year split, verified individual repeat count or detector q calibration. These permutations assume interaction tokens exchangeable within bat or plant, an unverified biological independence condition.

Original-author paper *Stratified sampling enhances the understanding of bat–fruit networks in the southern Atlantic Forest*, DOI `10.1002/oik.11609`. Capture level is **not the fruit-eating height**. All work remains on independent, unmerged prospective branch.
