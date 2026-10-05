# Training-process directional transfer v4: CV3max jackknife IUT

V4 is a new route candidate after three prospectively recorded predecessors.

- V1 controlled the null but failed its frozen power gate.
- V2 changed the compound composition to an intersection-union test and largely
  restored power, but its studentized component tests were mildly liberal.
- V3 removed studentization and passed the frozen power gate in all six
  scenarios, but its centered pigeonhole component intervals remained liberal
  under several small-cluster regimes.

V4 retains the same process-mean estimand and the same IUT composition. It
changes only the component variance estimator and critical value.

For one validation group and one information contrast, arrange the weighted
score-gain numerators as a complete R x B array: R frozen training-process draws
by B positive-mass validation blocks. The full estimate is the total numerator
divided by R times the total validation-block mass.

V4 computes three delete-one jackknife variances:

1. omit each training-process draw in turn;
2. omit each validation block in turn;
3. omit each refit x validation-block intersection cell in turn.

For each dimension J, the CV3 jackknife variance is

    V_J = (J-1)/J * sum_j (theta_minus_j - theta_hat)^2.

The three-term two-way variance is V_R + V_B - V_I. The scalar CV3max variance
used by v4 is

    max(V_R + V_B - V_I, V_R, V_B).

The component standard error is its square root. Each one-sided component lower
bound uses a Student-t critical value with min(R,B)-1 degrees of freedom. The
reported non-skippable ceiling advances only when every required component lower
bound exceeds the declared tolerance.

This follows the scalar CV3max / max-SE construction implemented by
MacKinnon, Nielsen, and Webb for two-way cluster jackknife inference. Their
finite-sample evidence motivates the method choice but does not qualify ODSP's
weighted-ratio process-mean endpoint. V4 therefore faces the same six prospective
null scenarios and the same 5-oracle-SE terminal-power >= 0.80 gate used for its
predecessors.

The v4 contracts were frozen before any v4 calibration result was opened. No
existing fixed-set or historical empirical result is reclassified.
