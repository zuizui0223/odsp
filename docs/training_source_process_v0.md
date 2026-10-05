# Training-source process v0: the next upstream uncertainty layer

The qualified training-process v5 route closes uncertainty over model refitting
**conditional on one frozen empirical training source**:

```text
E[r | S] E[v] D
```

where `S` is fixed, `r` is a draw from the frozen training-resampling process
and `v` is the validation population represented by validation blocks.

The next distinct question is:

```text
E[s] E[r | s] E[v] D
```

where `s` is now a draw from a separately predeclared **outer training-source
resampling process**.

This is a new estimand and therefore a new route. It does not reinterpret v5,
the fixed-set route or any historical empirical endpoint.

## Why another ordinary bootstrap is not enough

The dependence structure is no longer a simple crossed refit × validation
array.

- outer source draws are independent process draws;
- multiple inner model refits are nested within each source draw;
- the same validation blocks are crossed with every source draw and every inner
  refit.

Treating all inner refits as independent training-side observations would make
an outer source draw with many refits count as many independent source samples.
That is pseudoreplication.

Hierarchical bootstrap work makes the same general point for multilevel data:
resampling must respect the nesting level that carries independent information.
Multiway bootstrap/jackknife work separately shows how crossed cluster axes
must be retained rather than flattened.

References motivating the dependence structure, not qualifying this ODSP
endpoint:

- Saravanan et al. (2020), *Application of the hierarchical bootstrap to
  multi-level data in neuroscience*.
- Davezies, D'Haultfoeuille & Guyonvarch, *Asymptotic results under multiway
  clustering*.
- MacKinnon, Nielsen & Webb, *Jackknife inference with two-way clustering*.

## Candidate v0 reduction

For outer source draw `s`, validation block `b`, group `g` and contrast
`c`, first average over the fixed number `R` of inner refits:

```text
D_bar[s,b,g,c] = mean_r D[s,r,b,g,c].
```

The inner refits estimate `E[r | s]`; they do not create additional outer
source clusters.

The resulting array is source draw × validation block. V0 therefore proposes to
reuse the successful **structure** of v5 at this outer level:

```text
V_candidate = V_source^JK + V_validation^JK
df          = min(S, B) - 1
```

with the same one-sided component logic and intersection-union composition.

This is only a candidate. The v5 calibration cannot be borrowed because the
training-side observation is now an inner-refit average from a nested process.

## Why equal source-draw weighting is mandatory

Every outer source draw represents one draw from the source-resampling process.
It receives one unit of outer weight.

A source draw with 20 inner refits must not count twice as much as a source draw
with 10 refits. V0 therefore initially requires a fixed balanced inner-refit
count and averages within source before any outer inference.

Unbalanced inner-refit counts are outside v0 scope.

## What v0 does and does not generalize over

V0 would target a **declared source-resampling process**. That process can be
scientifically useful, but it is still a process-defined target.

It does not automatically establish inference over an unknown ecological
superpopulation that generated the original training source. Such a claim would
require a defensible original sampling design, inclusion mechanism or explicit
population model.

This distinction is deliberate:

```text
v5:
fixed empirical source
    -> training-resampling process
    -> validation population

v0 candidate:
outer source-resampling process
    -> nested training-resampling process
    -> validation population

not claimed:
unknown ecological source superpopulation
    -> ...
```

## Prospective qualification

Before any promotion, v0 must pass a new frozen operating-characteristic panel.
At minimum it must separate:

- source-dominant variance;
- inner-refit-dominant variance;
- validation-dominant variance;
- source × validation interaction;
- heavy tails;
- balanced mixed variance.

The null component-size gate remains the same Monte-Carlo tolerance used for v5,
and the frozen 5-oracle-SE terminal-power threshold remains 0.80.

A failure closes v0. Thresholds or scenarios may not be changed after opening the
result to rescue the same version.

## Governance

No route key is registered yet.

Before any future primary status, ODSP would need separate provenance for:

1. the outer source-resampling process;
2. generation of each outer source draw;
3. managed inner-refit generation nested under each source draw;
4. whole original source-frame separation from validation;
5. the qualified implementation/runtime identity.

This work therefore begins from the same rule that made the v5 chain defensible:
**different estimand, separate route, prospective evidence, no historical
reclassification.**
