# Thiel Bat camera resource height V3 independent numerical audit (after v2 result)

**Post-outcome code arithmetic verification only**; no new scientific hypothesis and no changed model. The first full original response v2 [run #45096400185](https://github.com/zuizui0223/odsp/actions/runs/45096400185), artifact 14783467426, and unchanged-source regression run [#45096424398](https://github.com/zuizui0223/odsp/actions/runs/45096424398) established **9 Marcgravia plants, 25 positive-effort paired source strata and 5,421 recorded Bat visits** with source-authenticated original Camera/Nectar XLSX, original checksum-pinned 2024 Thiel v2. Every training-only resource β fell back to exactly 0 under the **previously frozen** beta grid and ridge 0.02, and equal-plant B1−B0 = 0, all 9 zero, initial report and [v2 closeout](nectarivore_bat_plant_nectar_v2_original_heldout_zero_closeout.md).

This V3 makes an **independent fixed-grid optimization and scoring engine using NumPy**, not importing/calling the V2 `odsp/nectarivore_bat_resource_transfer_v2.py` `score_plant`, `fit` or `evaluate`. It may reuse the same original Zenodo XLSX **source adapter and checksum-based selected-plant reconstruction** because verification target is numerical scoring, not independent source discovery. The verifier re-downloads the same unchanged original XLSX bytes and accepts no alternative source.

For each of the nine leave-original-plant-out folds, reproduce exactly the original static model:
- same positive original Camera `Hours×Inflorescences`, original `Abundance` counted visits, log1p(original nectar quantity);
- B0 model layer α_mid, α_high and 0 resource coefficient; B1 α_mid, α_high + β x, fixed α/β 9-point grids [-2,2] in steps of 0.5, training mean count-weighted log score minus fixed 0.02×β²;
- deterministic objective/tie-breaking as frozen, compare original per-fold B0, B1, β and all aggregate results to tolerance 1e−10, with **no alternate penalty or resource column**.
- verify source 9 plants, 25 source layers and 5,421 Bat visits, no target leakage.
- any numerical disagreement triggers VERIFICATION_STOP, not a new claim. Any source access stop leaves original first v2 results unchanged.

This V3 is an independent **implementation audit**, not a second ecological dataset or independent field study. It cannot validate biological detection q, causal nectar influence, Bat species-level niche or larger generality; the trial remains a **fixed-model failure to improve predictive likelihood**.
