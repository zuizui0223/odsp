# Training-process directional transfer v3: centered pigeonhole IUT

V1 and v2 remain closed on their original prospective gates. V1 controlled the
global null but was too conservative to pass the frozen terminal-power gate. V2
changed only the compound composition to an intersection-union test; this
restored strong power, but several component tests exceeded the prospectively
frozen one-sided size tolerance.

V3 keeps the same process-mean estimand and the IUT composition. It changes the
component pivot.

For each validation group and ordered information contrast, the point estimator
is the mean gain over the crossed training-process x validation-block array.
Every bootstrap replicate independently resamples the training-process rows and
validation-block columns. The same training-row resample is shared across all
cells, and each group's validation-block resample is shared across its refits and
contrasts.

V3 does not studentize. For a component estimate theta_hat and pigeonhole
replicates theta_star, it uses the centered displacement distribution

    theta_star - theta_hat

and the one-sided basic lower bound

    L = theta_hat - q_0.95(theta_star - theta_hat).

The empirical quantile uses the conservative "higher" rule.

The compound ceiling is an intersection-union test: every required component
must have L above the declared tolerance. The component bounds are not
simultaneous confidence bounds and cannot support arbitrary post-hoc cellwise
discoveries.

The choice of a centered pigeonhole bootstrap is theory-motivated rather than
result-tuned. Multiway bootstrap theory establishes the pigeonhole resampling
scheme for separately exchangeable arrays and smooth estimators; ODSP still
requires its own prospective null and power panels for this exact directional
ratio/IUT endpoint.

The v3 null and power contracts were frozen before opening v3 calibration
results. They retain the same six uncertainty regimes, the same 0.05 component
size target, and the same 5-oracle-SE terminal-power >= 0.80 gate used for v2.
