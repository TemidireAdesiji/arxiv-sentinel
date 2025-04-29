"""Top-level test fixtures shared across all test layers."""

from __future__ import annotations

import pytest

from sentinel.settings import AppSettings


@pytest.fixture()
def app_cfg() -> AppSettings:
    """Minimal settings for unit/API tests."""
    return AppSettings(
        debug=True,
        environment="test",
        db_url="sqlite:///test.db",
        jina_api_key="test-key",
    )
