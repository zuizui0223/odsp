# V3 independent audit of the first whole-study holdout result (2026-11-23)

**Source already opened** in original V2 [successful run #45084122700](https://github.com/zuizui0223/odsp/actions/runs/45084122700), artifact 14778054983. Original source filename and Git SHA are unchanged. The first registered result must **not** be overwritten by any independent-check finding.

The original V2 used 127 original site×metric profiles, averaging 14 duplicate-height site profiles/49 extra rows; **54 abundance studies** and **42 richness studies** held out, study-equal. Aggregate: abundance gain **+0.0190802411910 nats/normalized site proxy**, 32/54 positive and descriptive study interval [-0.00385007,+0.04310444]; richness gain **+0.00200238055060**, 25/42 positive, interval [-0.00219696,+0.00594164]. Both are **mixed**. Bats abundance +0.03591887358 (12/21 positives, CI crosses zero), richness +0.00166644297 (7/12, CI crosses zero). This is not an identified 3D organism SDM.

Independent replay shall download the unchanged Git-pinned original study source and independently derive the same target profiles using a **different CSV reader and NumPy vectorized entropy/logsumexp scorer**, independently select the deterministic 49-beta grid study-equal fit and predict each heldout original study, and reproduce for both endpoints:
- original site profile counts (127 overall, 69 abundance, 58 richness),
- original distinct heldout studies (54 abundance, 42 richness),
- exact per-original-study paired mean B1−B0 gains, base and taxon slope training-only, with *no* original-study train/test leakage,
- original overall equal-study gains and bat-specific gains to abs tolerance 1e−9,
- no new new-tail-selection, cutoff or penalty alteration.

The separate implementation **must not import or call** V2 predictor, source reader, scorer, or study split utilities. It may import independent third-party `numpy`. If mismatches arise, do not retune to force favorable gains: preserve the original V2 score, identify a methodological bug, and determine if a corrected result (not a "replication") is required. No additional hypothesis tests or success thresholds beyond numerical consistency.

All prior source-level preregistration and negative/mixed claim boundaries remain unchanged. This is a **method/code verification**, not an independent ecological dataset.
