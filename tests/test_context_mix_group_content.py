"""Known-truth checks for context-mixture invariance and robust content."""
from collections.abc import Mapping
from dataclasses import replace
from fractions import Fraction
import json
from math import comb

import pytest

from odsp.common_input_transport import CLASSES, freeze_common_input_transport
from odsp.identity_checked_transport import freeze_identity_checked_transport
from odsp.context_mix_group_content import (
    ROBUST_IID, _summarize_context_masses,
    freeze_context_mix_content, assess_context_mix_content,
)


SPECIES = "Circus pygargus"


def fixture(n=29, day_weight=9., missing_cal=False, missing_val=False):
    # The training learner gives high scores to low state in clock context 1,
    # high state in context 0. Target records are entirely fabricated.
    train, cal, val = [], [], []
    for i in range(3):
        for j in range(8):
            day = j % 2 == 0
            train.append({
                "row_id": f"train_{i}_{j}",
                "individual-local-identifier": f"train_{i}",
                "individual-taxon-canonical-name": SPECIES,
                "timestamp": "2025-06-08T11:00:00Z" if day else "2025-06-08T23:00:00Z",
                "location-long": 4.35,
                "height-above-msl": 10.0 if day else 750.0,
            })
    for role, count, rows in (("cal", n, cal), ("val", 1, val)):
        for i in range(count):
            for ctx in (0, 1):
                if ctx == 0 and i == 0 and (
                    (role == "cal" and missing_cal) or (role == "val" and missing_val)
                ):
                    continue
                rows.append({
                    "row_id": f"{role}_{i}_{ctx}",
                    "individual.global.identifier": f"{role}_{i}",
                    "individual.taxon.canonical.name": SPECIES,
                    "timestamp": "2025-06-08T11:00:00Z" if ctx else "2025-06-08T23:00:00Z",
                    "location.long.rnd": 4.3,
                    "weight": day_weight if ctx else 1.,
                })
    transport = freeze_common_input_transport(
        training_BOP_rows=train, calibration_Dryad_features=cal,
        validation_Dryad_features=val, evidence_role="known_truth_synthetic_only",
    )
    model = transport.forecast
    metadata = {}
    for role, rows in (
        ("training", model.training_rows), ("calibration", model.plan.calibration_rows),
        ("validation", model.plan.validation_rows),
    ):
        source = "BOP" if role == "training" else "DRYAD"
        metadata[role] = [
            {"group_id": g, "entity_key": f"PRIVATE/{role}/{g}", "stratum": SPECIES,
             "source": source, "study_cluster": "training" if role == "training" else "target"}
            for g in sorted({r.group_id for r in rows})
        ]
    checked = freeze_identity_checked_transport(
        transport, training_metadata=metadata["training"],
        calibration_metadata=metadata["calibration"],
        validation_metadata=metadata["validation"], evidence_role="known_truth_synthetic_only",
    )
    labels = {
        r["row_id"]: CLASSES[0] if r["row_id"].endswith("_1") else CLASSES[-1]
        for r in cal
    }
    return checked, labels


def freeze(checked, minimum=1):
    return freeze_context_mix_content(
        checked, stratum=SPECIES, minimum_rows_per_context=minimum,
        sampling_assumption=ROBUST_IID,
    )


class Poison(Mapping):
    def __init__(self, keys):
        self.keys_only = tuple(keys)
        self.reads = 0

    def __iter__(self):
        return iter(self.keys_only)

    def __len__(self):
        return len(self.keys_only)

    def __getitem__(self, key):
        self.reads += 1
        raise AssertionError("outcome value opened before gate")


def test_mixture_flip_from_weights_alone():
    out = []
    for day_weight in (9., 1/9):
        checked, labels = fixture(day_weight=day_weight)
        # Same unfavorable outside-window labels and favorable inside labels
        # in both cohorts. Only observed context mass differs.
        labels = dict.fromkeys(labels, CLASSES[0])
        out.append(assess_context_mix_content(freeze(checked), labels))
    a,b = out
    assert a["observed_positive_groups"] == 29
    assert b["observed_positive_groups"] == 0
    assert a["equal_animal_mean_observed_gain"] > 0 > b["equal_animal_mean_observed_gain"]
    assert a["equal_animal_mean_balanced_gain"] == b["equal_animal_mean_balanced_gain"]
    assert a["equal_animal_mean_worst_mixture_gain"] == b["equal_animal_mean_worst_mixture_gain"]
    for x in out:
        assert x["context0_positive_groups"] == 0
        assert x["context1_positive_groups"] == 29
        assert x["all_mixtures_positive_groups"] == 0
        assert x["mixture_sensitive_groups"] == 29
        assert x["robust_content_p_value_upper_bound"] == 1
        assert x["status"] == "NOT_SUPPORTED"
        assert x["equal_context_positive_groups"] == 0


def test_all_contexts_robust_for_29_groups_supports_primary_only():
    checked, labels = fixture()
    policy = freeze(checked)
    assert policy.as_public_dict()["status"] == "COUNT_AND_CONTEXT_FEASIBLE_ONLY"
    x = assess_context_mix_content(policy, labels)
    assert x["all_mixtures_positive_groups"] == 29
    assert x["status"] == "SUPPORTED_IF_ROBUST_IID_HOLDS"
    assert x["robust_content_p_value_upper_bound"] == pytest.approx(float(Fraction(9,10)**29))
    assert x["validation_labels_accessed"] is False
    assert x["iid_or_biological_independence_verified_by_software"] is False
    assert x["real_dryad_admitted"] is False
    s = json.dumps(x)
    assert "PRIVATE/" not in s and "identity_sha256" not in s and "cal_0_0" not in s


def test_two_marginal_content_passes_do_not_imply_joint_robust_content():
    checked, labels = fixture(n=46)
    labels["cal_0_0"] = CLASSES[0]
    labels["cal_1_1"] = CLASSES[-1]
    result = assess_context_mix_content(freeze(checked), labels)
    assert result["context0_positive_groups"] == 45
    assert result["context1_positive_groups"] == 45
    assert result["all_mixtures_positive_groups"] == 44
    tails = [sum(Fraction(comb(46,j)*9**(46-j),10**46)
                 for j in range(k+1)) for k in (1,2)]
    assert tails[0] <= Fraction(1,20) < tails[1]
    assert result["status"] == "NOT_SUPPORTED"
    assert result["robust_content_p_value_upper_bound"] == pytest.approx(float(tails[1]))


@pytest.mark.parametrize("kwargs,minimum,status", [
    ({"n":9},1,"HOLD_INSUFFICIENT_GROUPS_FOR_CONTENT"),
    ({"missing_cal":True},1,"HOLD_INCOMPLETE_CONTEXT_SUPPORT"),
    ({"missing_val":True},1,"HOLD_INCOMPLETE_CONTEXT_SUPPORT"),
    ({},2,"HOLD_INCOMPLETE_CONTEXT_SUPPORT"),
])
def test_whole_roster_stops_before_any_labels(kwargs, minimum, status):
    checked, labels = fixture(**kwargs)
    policy = freeze(checked, minimum)
    assert policy.as_public_dict()["status"] == status
    poison = Poison(labels)
    with pytest.raises(ValueError, match=status):
        assess_context_mix_content(policy, poison)
    assert poison.reads == 0


@pytest.mark.parametrize("bad_key", ["extra","missing","validation"])
def test_role_keys_checked_before_value_access(bad_key):
    checked, labels = fixture()
    keys = set(labels)
    if bad_key == "missing":
        keys.remove("cal_0_0")
    else:
        keys.add("val_0_0" if bad_key=="validation" else "unexpected")
    poison = Poison(keys)
    with pytest.raises(ValueError, match="exact frozen native"):
        assess_context_mix_content(freeze(checked), poison)
    assert poison.reads == 0


def test_labels_read_once():
    checked, labels = fixture()
    reads = set()

    class Once(Mapping):
        def __iter__(self):
            return iter(labels)

        def __len__(self):
            return len(labels)

        def __getitem__(self,k):
            assert k not in reads
            reads.add(k)
            return labels[k]

    result = assess_context_mix_content(freeze(checked), Once())
    assert result["all_mixtures_positive_groups"] == 29
    assert reads == set(labels)


def test_tampered_policy_rejected_before_labels():
    checked, labels = fixture()
    p = replace(freeze(checked), minimum_rows_per_context=2)
    poison = Poison(labels)
    with pytest.raises(ValueError,match="policy or frozen support"):
        assess_context_mix_content(p,poison)
    assert poison.reads == 0


def test_artifact_tampering_rejected_before_labels():
    checked, labels = fixture()
    policy = freeze(checked)
    tampered = replace(
        checked, transport=replace(checked.transport, forecast=replace(
            checked.transport.forecast, model_artifact=b"altered",
        ))
    )
    poison = Poison(labels)
    with pytest.raises(ValueError):
        assess_context_mix_content(replace(policy,identity_checked=tampered), poison)
    assert poison.reads == 0


def test_context_feature_tampering_rejected_before_labels():
    checked, labels = fixture()
    policy = freeze(checked)
    forecast = checked.transport.forecast
    first,*rest = forecast.calibration_features
    tampered = replace(
        checked, transport=replace(checked.transport, forecast=replace(
            forecast, calibration_features=(replace(first,context=1-first.context),*rest),
        ))
    )
    poison = Poison(labels)
    with pytest.raises(ValueError):
        assess_context_mix_content(replace(policy,identity_checked=tampered), poison)
    assert poison.reads == 0


@pytest.mark.parametrize("minimum", [0, -1, True, 1.5, "2"])
def test_invalid_minimum_rejected(minimum):
    checked,_ = fixture()
    with pytest.raises(ValueError, match="positive integer"):
        freeze(checked, minimum)


def test_explicit_robust_iid_and_one_stratum_required():
    checked,_ = fixture()
    with pytest.raises(ValueError,match="robust group indicator"):
        freeze_context_mix_content(checked,stratum=SPECIES,minimum_rows_per_context=1,
                                   sampling_assumption="iid_group_gains_within_prespecified_stratum")
    with pytest.raises(ValueError,match="exactly one target"):
        freeze_context_mix_content(checked,stratum="Buteo buteo",minimum_rows_per_context=1,
                                   sampling_assumption=ROBUST_IID)


def test_exact_weighted_context_sign_tie_and_subnormal_weights():
    tiny = float.fromhex("0x0.0000000000001p-1022")
    g = _summarize_context_masses([(0,1.0,tiny),(0,-1.0,tiny),(1,.5,tiny)])
    assert g.context0 == g.worst == 0
    assert g.context1 == Fraction(1,2)
    assert g.observed == Fraction(1,6)
    assert g.balanced == Fraction(1,4)
    assert not g.worst > 0


def test_exact_endpoints_bound_every_rational_mixture():
    g = _summarize_context_masses([(0,1.,1.),(0,2.,3.),(1,-1.,2.)])
    for i in range(101):
        w = Fraction(i,100)
        mix = (1-w)*g.context0+w*g.context1
        assert g.worst <= mix <= g.best
    assert g.worst == -1
    assert g.best == Fraction(7,4)


@pytest.mark.parametrize("rows", [
    [(0,1.,1.)], [(1,1.,1.)], [(2,1.,1.)], [(True,1.,1.)],
    [(0,float("inf"),1.)], [(0,1.,0.)], [(0,1.,-1.)],
])
def test_invalid_group_context_mass_refused(rows):
    with pytest.raises(ValueError):
        _summarize_context_masses(rows)
