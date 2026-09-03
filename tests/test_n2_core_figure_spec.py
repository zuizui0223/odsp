import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str) -> dict[str, object]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_core_figure_uses_exact_terminal_matrix_values():
    matrix = _load("N2_EMPIRICAL_STATE_MATRIX.json")["lanes"]
    figure = _load("N2_CORE_FIGURE_SPEC.json")["panels"]

    bat = matrix["european_free_tailed_bat"]
    bat_metrics = figure["B"]["metrics"]
    assert bat_metrics["H_Z_given_XY_nats"] == bat["added_axis_thickness"]["information_nats"]
    assert bat_metrics["effective_vertical_states"] == bat["added_axis_thickness"]["effective_states"]
    assert bat_metrics["heldout_gains"] == bat["independent_transferability"]["gains"]

    serengeti = matrix["snapshot_serengeti"]
    temporal = figure["C"]["metrics"]
    assert temporal["admitted_species"] == serengeti["admitted_species_count"]
    assert temporal["H_T_given_Site_nats"] == serengeti["added_axis_thickness"]["information_nats"]
    assert temporal["effective_temporal_states"] == serengeti["added_axis_thickness"]["effective_states"]
    assert temporal["I_Species_T_given_Site_nats"] == serengeti["conditioned_organization"]["information_nats"]
    assert temporal["permutation_p_value"] == serengeti["conditioned_organization"]["permutation_p_value"]
    assert temporal["heldout_gains"] == serengeti["independent_transferability"]["gains"]


def test_panel_d_preserves_the_three_distinct_terminal_states():
    rows = _load("N2_CORE_FIGURE_SPEC.json")["panels"]["D"]["rows"]
    assert [row["independent_transferability"] for row in rows] == [
        "unavailable",
        "non_generalizing",
        "generalizing",
    ]


def test_figure_claim_ceiling_forbids_cross_system_axis_causality():
    ceiling = _load("N2_CORE_FIGURE_SPEC.json")["caption_claim_ceiling"]
    forbidden = " ".join(ceiling["forbidden"])
    assert "generally more stable" in forbidden
    assert "directly comparable" in forbidden
    assert "competition" in forbidden
    assert "N3 state map" in forbidden
