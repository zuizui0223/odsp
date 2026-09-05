from __future__ import annotations

from scripts.build_n2_mee_state_prediction_figures_v4 import figure_data


def test_figure_data_pins_known_truth_benchmark():
    data = figure_data()
    benchmark = data["benchmark"]
    assert benchmark["replicates_per_cell"] == 128
    assert benchmark["sample_sizes"] == [50, 250, 1000]
    assert benchmark["families"]["stable_generalizing"] == [
        0.30033855056322634,
        0.3200597635108605,
        0.32294219738413865,
    ]
    assert benchmark["families"]["shifted_non_generalizing"] == [
        -0.7823614748529366,
        -0.7809825601417892,
        -0.7733028576630449,
    ]


def test_figure_data_pins_bop_individual_transfer():
    data = figure_data()
    bop = data["bop"]
    assert bop["terminal_category"] == "empirical_state_prediction_mixed"
    assert bop["positive_count"] == 27
    assert bop["total_count"] == 30
    assert bop["positive_brier_count"] == 30
    assert bop["species"]["Buteo buteo"]["positive_count"] == 5
    assert bop["species"]["Buteo buteo"]["individual_count"] == 5
    assert bop["species"]["Circus pygargus"]["positive_count"] == 9
    assert bop["species"]["Circus pygargus"]["individual_count"] == 9
    assert bop["species"]["Circus aeruginosus"]["category"] == "mixed"
    assert bop["species"]["Circus cyaneus"]["category"] == "mixed"


def test_figure_data_keeps_individual_failures_visible():
    data = figure_data()
    gains = [
        gain
        for species in data["bop"]["species"].values()
        for gain in species["gains"]
    ]
    assert len(gains) == 30
    assert sum(g > 0 for g in gains) == 27
    assert sum(g <= 0 for g in gains) == 3
    assert min(gains) == -0.23078224313265183
    assert max(gains) == 1.499987587497081
