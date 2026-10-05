# Training-process directional transfer v2: IUT ceiling

V1 is closed as a failed candidate: its crossed null calibration passed, but its
predeclared 5-SE terminal-power gate failed in five of six scenarios. The v1
result is retained and is not rescued by changing the threshold after seeing the
power panel.

V2 keeps the inferential target, training-process definition, crossed bootstrap,
and two-way studentizer unchanged. It changes only how the required component
tests are composed.

The confirmatory claim is a conjunction: every validation group at every
information step required by the reported ceiling must have positive process-mean
gain. The null is therefore a union: at least one required component has
non-positive gain. V2 tests each component with a level-alpha one-sided crossed
bootstrap-t test and advances the ceiling only if every required component
rejects.

This is an intersection-union test. No independence among component tests and no
Bonferroni/max-t correction are required for the compound conjunction. If the
compound null is true, some component null is true; a false compound rejection
requires that true component test to reject, whose probability is bounded by
alpha.

The tradeoff is explicit: v2 component lower bounds are not simultaneous
confidence bounds. They must not be used for an arbitrary "which cells are
positive?" familywise discovery claim. The only candidate confirmatory output is
the predeclared compound non-skippable ceiling.

The first v2 qualification is frozen before opening v2 results. It reuses the
same six crossed uncertainty regimes and the same 5-oracle-SE terminal-power
threshold used by v1. The null gate changes to the operating characteristic
actually needed by the IUT: every component test must have one-sided size no
larger than the predeclared Monte Carlo tolerance. The any-cell false-positive
rate is diagnostic only.
