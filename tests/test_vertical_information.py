import pytest

from odsp.vertical_information import (
    VerticalFieldMap,
    gbif_locality_elevation_mapping,
    normalize_vertical_information,
)


def test_explicit_canopy_stratum_is_usable_categorical_niche_z():
    record = {"id": "obs-1", "layer": "upper_canopy"}
    result = normalize_vertical_information(
        "canopy_survey",
        record,
        VerticalFieldMap(
            axis_kind="canopy_stratum",
            stratum_field="layer",
            source_id_field="id",
        ),
    )
    assert result.source_occurrence_id == "obs-1"
    assert result.vertical_precision == "categorical"
    assert result.stratum_label == "upper_canopy"
    assert result.usable_as_niche_z is True


def test_measured_organism_height_preserves_reference_and_sensor_coverage():
    record = {
        "id": 7,
        "height_m": 3.2,
        "uncertainty_m": 0.4,
        "sensor_min_m": 0.0,
        "sensor_max_m": 5.0,
    }
    result = normalize_vertical_information(
        "camera_array",
        record,
        VerticalFieldMap(
            axis_kind="organism_height",
            value_field="height_m",
            default_unit="m",
            default_reference="ground",
            uncertainty_field="uncertainty_m",
            sensor_minimum_field="sensor_min_m",
            sensor_maximum_field="sensor_max_m",
            source_id_field="id",
        ),
    )
    assert result.value == pytest.approx(3.2)
    assert result.reference == "ground"
    assert result.uncertainty == pytest.approx(0.4)
    assert result.sensor_minimum == pytest.approx(0.0)
    assert result.sensor_maximum == pytest.approx(5.0)
    assert result.usable_as_niche_z is True
    assert "sensor_vertical_coverage_available" in result.vertical_quality_flags


def test_numeric_biological_z_without_unit_is_not_usable():
    result = normalize_vertical_information(
        "telemetry",
        {"depth": 8.0},
        VerticalFieldMap(
            axis_kind="organism_depth",
            value_field="depth",
            default_reference="water_surface",
        ),
    )
    assert result.vertical_precision == "point"
    assert result.usable_as_niche_z is False
    assert "vertical_unit_missing" in result.vertical_quality_flags


def test_gbif_locality_elevation_is_preserved_but_not_used_as_niche_z():
    result = normalize_vertical_information(
        "gbif",
        {
            "gbifID": "123",
            "minimumElevationInMeters": 500,
            "maximumElevationInMeters": 520,
        },
        gbif_locality_elevation_mapping(),
    )
    assert result.vertical_precision == "interval"
    assert result.minimum == pytest.approx(500)
    assert result.maximum == pytest.approx(520)
    assert result.unit == "m"
    assert result.reference == "sea_level"
    assert result.usable_as_niche_z is False
    assert "locality_elevation_is_not_within_cell_niche_z" in result.vertical_quality_flags


def test_sensor_height_is_observation_geometry_not_biological_z():
    result = normalize_vertical_information(
        "acoustic_sensor",
        {"sensor_height": 12.0},
        VerticalFieldMap(
            axis_kind="sensor_height",
            value_field="sensor_height",
            default_unit="m",
            default_reference="ground",
        ),
    )
    assert result.usable_as_niche_z is False
    assert "sensor_position_is_observation_geometry_not_organism_z" in result.vertical_quality_flags


def test_reversed_interval_fails_closed():
    result = normalize_vertical_information(
        "depth_logger",
        {"min_depth": 10.0, "max_depth": 2.0},
        VerticalFieldMap(
            axis_kind="organism_depth",
            minimum_field="min_depth",
            maximum_field="max_depth",
            default_unit="m",
            default_reference="water_surface",
        ),
    )
    assert result.minimum is None and result.maximum is None
    assert result.usable_as_niche_z is False
    assert "vertical_interval_reversed" in result.vertical_quality_flags


def test_vertical_mapping_requires_explicit_semantic_and_data_field():
    with pytest.raises(ValueError, match="unknown vertical axis"):
        VerticalFieldMap(axis_kind="guess_from_landcover", value_field="z")
    with pytest.raises(ValueError, match="at least one vertical data field"):
        VerticalFieldMap(axis_kind="organism_height")
