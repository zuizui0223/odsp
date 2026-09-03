# N2 Snapshot Serengeti temporal-partition terminal result — 2026-09-04

## Terminal status

The prospectively frozen Snapshot Serengeti lane is closed as:

**`temporal_partition_generalizing`**

The canonical validated receipt is `N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json`, with exact source-result fingerprint:

`106dbb65271e0c5f115f33570e39c0f3a48e5d0533a006c528e1fd3b981b4145`

## Frozen primary result

Seventeen species passed the outcome-blind frozen admission rules.

- `H(T|Site) = 1.6396235816361795` nats
- `exp(H(T|Site)) = 5.153229376935854` effective four-hour temporal states out of six fixed bins
- `I(Species;T|Site) = 0.22427598739601606` nats
- within-site permutation p-value = `0.005` from 199 frozen permutations
- held-out site-fold 0 gain = `0.0572411993741857`
- held-out site-fold 1 gain = `0.045158861333215006`
- held-out site-fold 2 gain = `0.04514355468571751`

All three independently held-out site-fold gains are positive, so the frozen transfer category is **`generalizing`**.

## Biological interpretation

The camera-detected mammal assemblage uses a broad temporal state space after site is known: about 5.15 effective states across the six fixed four-hour bins. Species identity also carries additional information about detected time within the same sites, and that species-conditioned temporal organization predicts all three independently held-out camera-site folds better than the identity-blind temporal marginal.

Thus this lane supplies a positive Chapter-2 example in which an added niche axis is not only descriptively thick but also contains identity-resolved organization that transfers to independent spatial sampling units.

This result complements, rather than repairs, the European free-tailed bat vertical lane. The bat lane showed substantial `H(Z|X,Y)` but non-generalizing x-y-conditioned vertical organization; the Serengeti lane shows substantial temporal thickness plus independently generalizing species-time organization. Together they demonstrate that **thickness magnitude and transferable organization are distinct empirical properties**.

## Claim ceiling

The result concerns **camera-detected local clock-time organization** under the frozen effort weighting and event-independence rules. It does not by itself establish:

- true underlying activity-time niche partition independent of time-varying detection;
- solar-time partitioning;
- interspecific competition, displacement, or another causal mechanism;
- cross-region, cross-season, or cross-dataset generality.

No post-outcome time-bin, species-admission, pseudocount, fold, dataset, or permutation retuning is authorized.

## N2 → N3 boundary

Despite `generalizing` transferability, this terminal receipt is a summary, not an integrity-pinned axis-resolved species-state artifact. Therefore:

- `axis_resolved_state_allowed_for_empirical_n3 = false`;
- no `n2-to-n3-payload-v1` empirical state payload is issued from this terminal summary;
- EOG/N3 must not infer or reconstruct a species × time state artifact from the summary alone.

A future N3 handoff would require a separately specified and integrity-pinned state artifact consistent with the existing handoff contract. The present N2 endpoint is complete without such promotion.

## Execution and recovery provenance

The original authoritative workflow run `33726030526` at frozen analysis SHA `d17a204527b5426d29535ef6303bc759fe52adcc` downloaded and checksum-verified the inputs and completed the frozen calculations in process memory, but failed while constructing the output dictionary because five executed result fields used JSON-style lowercase Python booleans. It uploaded no artifact and logged no raw terminal numeric result.

A technical recovery was frozen before numeric interpretation in `N2_SERENGETI_TECHNICAL_RECOVERY_CONTRACT.json`. Recovery run `33774650396` checked out the original analysis SHA, applied only those five predeclared serialization replacements, reverified the same source checksums, reran the same analysis, suppressed raw result output, and produced artifact `9901082589` with digest `sha256:4cbba5bc2f98e0967fa6a2db37ef0e2ab893e4ee0600491b4b6eb2a70231fc78`.

Closeout run `33775057303` pinned that artifact by ID, digest, recovery-run origin and head SHA, then passed it through the pre-existing fail-closed validator. It produced canonical receipt artifact `9901215081` with digest `sha256:25f525a03f3fdf4e2cfe1e6de617a58745d0bf09b1f79ba49269dbb45f68ee28`.

The technical recovery did not change any scientific estimand or frozen analysis choice.
