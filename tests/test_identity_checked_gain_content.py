"""Synthetic-only end-to-end population content admission and validation."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
import json

import pytest

from odsp.common_input_transport import (
    CLASSES, freeze_common_input_transport,
)
from odsp.identity_checked_transport import freeze_identity_checked_transport
from odsp.identity_checked_gain_content import (
    assess_identity_checked_gain_content,
    freeze_identity_checked_gain_content,
    validate_identity_checked_gain_content,
)

IID = "iid_group_gains_within_prespecified_stratum"
SPECIES = ("Buteo buteo", "Circus aeruginosus")


def fixture(n=29, multiple_strata=False):
    """Invented bird rows with an explicit day/night conditional state pattern."""
    train, cal, val = [], [], []
    for si, species in enumerate(SPECIES[:2 if multiple_strata else 1]):
        for i in range(3):
            for j in range(8):
                day = j % 2 == 0
                train.append({
                    "row_id": f"train_{si}_{i}_{j}",
                    "individual-local-identifier": f"train_{si}_{i}",
                    "individual-taxon-canonical-name": species,
                    "timestamp": "2025-06-08T11:00:00Z" if day
                        else "2025-06-08T23:00:00Z",
                    "location-long": 4.35,
                    "height-above-msl": 10.0 if day else 750.0,
                })
        for i in range(n):
            cal.append({
                "row_id": f"cal_{si}_{i}",
                "individual.global.identifier": f"cal_{si}_{i}",
                "individual.taxon.canonical.name": species,
                "timestamp": "2025-06-08T11:00:00Z",
                "location.long.rnd": 4.3,
            })
        val.append({
            "row_id": f"test_{si}",
            "individual.global.identifier": f"test_{si}",
            "individual.taxon.canonical.name": species,
            "timestamp": "2025-06-08T11:00:00Z",
            "location.long.rnd": 4.3,
        })
    transport = freeze_common_input_transport(
        training_BOP_rows=train,
        calibration_Dryad_features=cal,
        validation_Dryad_features=val,
        evidence_role="known_truth_synthetic_only",
    )
    by_role = {
        "training": {row.group_id: row.stratum for row in transport.forecast.training_rows},
        "calibration": {row.group_id: row.stratum for row in transport.forecast.plan.calibration_rows},
        "validation": {row.group_id: row.stratum for row in transport.forecast.plan.validation_rows},
    }
    metadata = {
        role: [
            {
                "group_id": group_id,
                "entity_key": f"CANONICAL_SYNTHETIC/{role}/{group_id}",
                "stratum": species,
                "source": "BOP" if role == "training" else "DRYAD",
                "study_cluster": "synthetic_train" if role == "training" else "synthetic_target",
            }
            for group_id, species in sorted(groups.items())
        ]
        for role, groups in by_role.items()
    }
    return transport, metadata, {r["row_id"]: CLASSES[0] for r in cal}, {
        r["row_id"]: CLASSES[-1] for r in val
    }


def admitted(n=29, multiple_strata=False):
    transport, metadata, cal, val = fixture(n, multiple_strata)
    checked = freeze_identity_checked_transport(
        transport,
        training_metadata=metadata["training"],
        calibration_metadata=metadata["calibration"],
        validation_metadata=metadata["validation"],
        evidence_role="known_truth_synthetic_only",
    )
    return checked, cal, val


def freeze(checked):
    return freeze_identity_checked_gain_content(
        checked,
        stratum=SPECIES[0], sampling_assumption=IID,
    )


class PoisonedValues(Mapping):
    def __init__(self, keys):
        self.keys_only = tuple(keys)
        self.reads = 0

    def __iter__(self):
        return iter(self.keys_only)

    def __len__(self):
        return len(self.keys_only)

    def __getitem__(self, key):
        self.reads += 1
        raise AssertionError("label opened before upstream gate or role check")


def test_real_managed_fit_to_canonical_identity_to_content_then_untouched_negative():
    checked, cal, val = admitted()
    binding = freeze(checked)
    public = binding.as_public_dict()
    assert public["calibration_group_count"] == 29
    assert public["validation_group_count"] == 1
    assert public["count_allows_support"] is True
    assert public["managed_model_and_forecasts_replayed"] is True
    assert public["biological_iid_sampling_proven_by_software"] is False
    assert public["real_Dryad_external_candidate_admitted"] is False
    assert "CANONICAL_SYNTHETIC" not in json.dumps(public)
    assert "identity_fingerprint_sha256" not in public  # private crosswalk hash

    result = assess_identity_checked_gain_content(binding, cal)
    assert result.content.supported is True
    assert result.content.nonpositive_group_count == 0
    assert result.content.calibration.calibration_sha256 == result.as_public_dict()["calibration_sha256"]
    assert "CANONICAL_SYNTHETIC" not in json.dumps(result.as_public_dict())
    assert "identity_fingerprint_sha256" not in result.as_public_dict()
    outcome = validate_identity_checked_gain_content(binding, result, val)
    assert outcome.validation_group_count == 1
    assert outcome.strata[0].positive_validation_group_count == 0
    assert result.content.supported is True  # validation cannot retune the content test


def test_nine_groups_pass_rank_identity_but_not_content_before_any_labels():
    checked, _, _ = admitted(n=9)
    assert checked.admission.strata[0].one_sided_lower_rank == 1
    binding = freeze(checked)
    assert not binding.content_plan.count_allows_support
    poison = PoisonedValues(["cal_0_0"])
    with pytest.raises(ValueError, match="insufficient independent calibration"):
        assess_identity_checked_gain_content(binding, poison)
    assert poison.reads == 0


def test_one_nonpositive_group_prevents_support_at_29():
    checked, cal, _ = admitted()
    cal["cal_0_0"] = CLASSES[-1]
    result = assess_identity_checked_gain_content(freeze(checked), cal)
    assert result.content.nonpositive_group_count == 1
    assert not result.content.supported


@pytest.mark.parametrize("role_error", ["validation", "missing", "unplanned"])
def test_wrong_role_ids_rejected_without_any_label_values(role_error):
    checked, cal, _ = admitted()
    keys = set(cal)
    if role_error == "validation":
        keys.add("test_0")
    elif role_error == "missing":
        keys.remove("cal_0_0")
    else:
        keys.add("unplanned")
    poison = PoisonedValues(keys)
    with pytest.raises(ValueError, match="native calibration row IDs"):
        assess_identity_checked_gain_content(freeze(checked), poison)
    assert poison.reads == 0


def test_calibration_values_read_once_for_correct_role():
    checked, cal, _ = admitted()
    reads = set()

    class Once(Mapping):
        def __iter__(self):
            return iter(cal)

        def __len__(self):
            return len(cal)

        def __getitem__(self, key):
            if key in reads:
                raise AssertionError("calibration label reread")
            reads.add(key)
            return cal[key]

    result = assess_identity_checked_gain_content(freeze(checked), Once())
    assert result.content.supported
    assert reads == set(cal)


def test_multiple_target_strata_refused_before_selected_stratum_values():
    checked, _, _ = admitted(multiple_strata=True)
    with pytest.raises(ValueError, match="exactly one target"):
        freeze(checked)


def test_identity_reuse_across_different_group_ids_is_blocked_before_binding():
    transport, metadata, _, _ = fixture()
    metadata["calibration"][0]["entity_key"] = metadata["training"][0]["entity_key"]
    with pytest.raises(ValueError, match="canonical animal entity reused"):
        freeze_identity_checked_transport(
            transport,
            training_metadata=metadata["training"],
            calibration_metadata=metadata["calibration"],
            validation_metadata=metadata["validation"],
            evidence_role="known_truth_synthetic_only",
        )


def test_private_identity_tampering_fails_before_calibration_labels():
    checked, cal, _ = admitted()
    binding = freeze(checked)
    records = list(checked.group_records_by_role)
    role, individuals = records[0]
    records[0] = (role, (
        replace(individuals[0], entity_key="FALSIFIED_CANONICAL_ID"),
        *individuals[1:],
    ))
    tampered = replace(binding, identity_checked=replace(
        checked, group_records_by_role=tuple(records),
    ))
    poison = PoisonedValues(cal)
    with pytest.raises(ValueError, match="snapshot changed"):
        assess_identity_checked_gain_content(tampered, poison)
    assert poison.reads == 0


def test_managed_training_artifact_tampering_fails_before_calibration_labels():
    checked, cal, _ = admitted()
    binding = freeze(checked)
    changed_forecast = replace(checked.transport.forecast, model_artifact=b"changed")
    changed_transport = replace(checked.transport, forecast=changed_forecast)
    tampered = replace(binding, identity_checked=replace(
        checked, transport=changed_transport,
    ))
    poison = PoisonedValues(cal)
    with pytest.raises(ValueError, match="replay mismatch"):
        assess_identity_checked_gain_content(tampered, poison)
    assert poison.reads == 0


def test_content_policy_tampering_fails_before_calibration_labels():
    checked, cal, _ = admitted()
    binding = freeze(checked)
    altered = replace(binding, content_plan=replace(
        binding.content_plan, gain_threshold=1.0,
    ))
    poison = PoisonedValues(cal)
    with pytest.raises(ValueError, match="content policy"):
        assess_identity_checked_gain_content(altered, poison)
    assert poison.reads == 0


def test_result_cannot_be_used_with_other_content_binding():
    checked, cal, val = admitted()
    binding = freeze(checked)
    result = assess_identity_checked_gain_content(binding, cal)
    other = freeze_identity_checked_gain_content(
        checked, stratum=SPECIES[0], sampling_assumption=IID,
        gain_threshold=0.01,
    )
    with pytest.raises(ValueError, match="another identity binding"):
        validate_identity_checked_gain_content(other, result, val)


def test_forged_content_event_count_or_tail_fails_before_validation_labels():
    checked, cal, val = admitted()
    binding = freeze(checked)
    result = assess_identity_checked_gain_content(binding, cal)
    forged = replace(result, content=replace(
        result.content, nonpositive_group_count=1,
    ))
    poison = PoisonedValues(val)
    with pytest.raises(ValueError, match="exact content decision"):
        validate_identity_checked_gain_content(binding, forged, poison)
    assert poison.reads == 0


def test_wrong_validation_role_stops_without_reading_any_test_label():
    checked, cal, val = admitted()
    binding = freeze(checked)
    result = assess_identity_checked_gain_content(binding, cal)
    poison = PoisonedValues([*val, "cal_0_0"])
    with pytest.raises(ValueError, match="only exact frozen Dryad role"):
        validate_identity_checked_gain_content(binding, result, poison)
    assert poison.reads == 0
