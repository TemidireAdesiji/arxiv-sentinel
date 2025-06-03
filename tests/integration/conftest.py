"""Integration-test fixtures (requires running services)."""

from __future__ import annotations

import pytest


def pytest_collection_modifyitems(config, items):
    """Auto-mark every test in this directory as integration."""
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
