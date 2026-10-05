# Training-process directional transfer v5: two-term CV3 jackknife IUT

V5 is a distinct literature-defined jackknife candidate, not a post-hoc change
to the acceptance threshold of any predecessor.

For every group x ordered information contrast, V5 uses the same delete-one
training-refit and delete-one validation-block jackknife components as the
CV3 family:

    V_R = (R-1)/R * sum_r (theta_minus_r - theta_hat)^2
    V_B = (B-1)/B * sum_b (theta_minus_b - theta_hat)^2.

The component variance is the two-term estimator

    V_CV3(2) = V_R + V_B.

No intersection variance is subtracted. The one-sided lower bound uses a
Student-t critical value with min(R,B)-1 degrees of freedom. The global
non-skippable claim remains an intersection-union test: every required component
must reject its one-sided null.

The two-term estimator is an existing member of the two-way cluster-jackknife
family. It is expected to be conservative in some dependence regimes, so V5
retains the same prospective power requirement as V1-V4 instead of treating
conservatism as automatically desirable.

The six null scenarios, component-size limit, standardized alternatives and
terminal-power gate are unchanged. V5 results were not opened before this
contract was frozen. Existing fixed-set and historical endpoints are untouched.
