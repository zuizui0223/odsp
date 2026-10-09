# Independent camera-trigger calibration: pay for its uncertainty

**Source-free synthetic calibration study; not original Uljin inference.**
The parent PR #247 asks whether a detected seasonal early/late odds ratio
survives an ASSUMED upper cap B on the detection-efficiency crossproduct.
Here B is instead learned conservatively from independent synthetic
reference-trigger trials under explicit simultaneous coverage, with its
statistical cost paid when making a behavioral/encounter claim.

## Two independent sampling experiments

1. Reference calibration: in each of four fixed cells (rising/falling
   photoperiod branch × preselected early/late solar-phase bin), an
   independently timestamped known true animal-passage opportunity is
   presented to the same detector configuration n times. Camera
   successes S_bk ~ Binomial(n,q_bk) are independent of each other and
   of the separate animal encounter counts.
2. Animal detections: independent cell Poisson arrivals have means
   E_bk A_bk q_bk where E is true independently logged camera on-time,
   A is latent encounter/pass-through rate and q is the calibrated
   conditional detection efficiency. Conditioning on animal season
   and phase-bin totals yields Fisher noncentral hypergeometric X,
   where theta_count=theta_E*theta_A*theta_q.

The four **simultaneous** q intervals use Hoeffding with
eps = sqrt(ln(8/alpha_cal)/(2*n)), alpha_cal=0.025:
 q_lower=max(0,S/n-eps), q_upper=min(1,S/n+eps).

The union bound guarantees true q lies in all four bands with
probability ≥0.975, under the binomial model (the observed 600-world
coverage fraction is NOT the coverage guarantee). If either denominator
cell lower limit is 0, no finite upper bound on the detector seasonal
crossproduct exists: declare HOLD rather than dividing by zero.

Otherwise B=q_fall_early^upper*q_rise_late^upper /
(q_rise_early^lower*q_fall_late^lower). For the one-sided null of
latent encounter seasonal OR≤1, the largest null detected-count odds
ratio is theta_E*B. The exact Fisher upper tail at this noncentrality
is compared with alpha_test=0.025, NOT 0.05. The calibration failure
risk 0.025 plus the independent animal-test rejection risk 0.025
bounds overall false certification by 0.05 (union bound).
The animal source must not influence the calibration sample selection,
which must represent the same target species, trajectories, season
and phase-dependent detector response to transfer this guarantee.

## First fixed simulation panel

Four frozen worlds: (a) neutral q, no encounter shift; (b) neutral q,
camera-hour imbalance only; (c) detector seasonal crossproduct=2 but
NO animal encounter shift; (d) actual latent encounter OR=2, neutral q.
Each has fixed original artificial season/phase event totals and
independent reference calibration true q. Four n levels: 50, 200,
1000, 5000 known reference passage opportunities PER each calibration
cell; 600 independent fixed-seed Monte Carlo paired calibration/animal
experiments per world/n = 9600 source-free worlds.

For animal events in each world, use the exact site-conditioned
noncentral hypergeometric law at theta_E theta_q theta_A,
maintaining its frozen row and column totals. For each independent
calibration sample, compute robust decision and an uncalibrated
detector-ignorant negative-control decision. Also report:
joint q band empirical coverage, prevalence of positive-q HOLD,
median finite B, and an exact 97.5% one-sided lower OR confidence
bound on a fixed illustrative count table (no model-selection).
This is CONDITIONAL sampling: source row/column margins were fixed,
not generated from a future animal population. There are no source
animal records or real detector calibration observations.

These four artificial worlds do not establish a real dataset's
detector sensitivity, transferability to different seasons/species,
sensor false-negative rate, actual independence of reference triggers,
or animal latent behavior. A separate observational field protocol
and source-specific frozen validation remain required.

The original 41 calendar date pairs, original clock/solar phase
likelihood, heldout ODSP source-process routes and all previous
synthetic outputs are left untouched.
