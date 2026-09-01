# Tawaki Gate D terminal status — empirical gate unavailable

Chapter: **N2 / ODSP — HOW THICK is it?**  
Contract: `odsp-gate-d-tawaki-v1`

## Terminal decision

**`empirical_gate_d_unavailable`**

The decision was reached from the prospectively frozen structural coverage/stratum gates **before any niche-thickness outcome was opened**.

The structural preflight was executed on the pinned public Tawaki sources under PR #14 and completed successfully as an operational run. Its receipt artifact is `gate-d-tawaki-structural-preflight` (artifact `9787831980`, digest `sha256:296b083ccfd8db7693d3ecc3ae4e6df630d421f2dc2da28feecd8fae45e21798`).

## Why the gate failed

The frozen 5 km primary grid required each site × year stratum to contain at least five estimable cells, with each estimable cell requiring at least 30 located events, three bird-trips and two birds.

| Site | Year | cells with located model-pool events | estimable cells | site-year gate |
|---|---:|---:|---:|---|
| Harrison Cove | 2019 | 8 | **0** | fail |
| Harrison Cove | 2020 | 11 | **0** | fail |
| Moraine | 2019 | 28 | **9** | pass |
| Moraine | 2020 | 42 | **8** | pass |

Across all processed qualifying dives, 3,880 of 32,668 were location-resolved under the source-linked table (`11.88%`). The key terminal fact is not the overall percentage but that the predeclared full site-year structural gate did not pass.

## What was not opened

No biological N2 outcome was calculated or inspected:

- no depth-bin frequency distribution;
- no `H(Z|X,Y)`;
- no `exp(H(Z|X,Y))`;
- no `axis_thickness_map` values;
- no projection-loss values;
- no sealed held-out log-score difference;
- no sealed bootstrap confidence interval.

Therefore this result **does not mean niche thickness is zero or unsupported**. It means only that this dataset, under this frozen primary design, cannot support the planned full-denominator empirical Gate-D claim.

## No rescue

The primary 5 km grid is not replaced by the 2.5 or 10 km sensitivity grid. Cell eligibility thresholds and depth bins are not relaxed. A reserve dataset is not substituted into the same Gate-D endpoint.

Gate E is **not authorized**, because its prospective prerequisite was successful empirical estimability at Gate D.

Any future empirical N2 validation must be a new, separately frozen programme and must retain this Tawaki result as `empirical_gate_d_unavailable`.
