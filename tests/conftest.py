from __future__ import annotations

import pytest

from test_lane_policy import classify_test_path


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Assign every collected test to exactly one repository lane."""

    for item in items:
        lane = classify_test_path(str(item.path))
        item.add_marker(getattr(pytest.mark, lane))
