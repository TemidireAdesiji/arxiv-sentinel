"""Tests for sentinel.settings — defaults and validation."""

from __future__ import annotations

import pytest

from sentinel.settings import AppSettings


class TestAppSettingsDefaults:
    def test_environment_from_env(self):
        cfg = AppSettings(
            db_url="sqlite:///x.db",
            jina_api_key="k",
        )
        assert cfg.environment in (
            "development",
            "test",
        )

    def test_debug_is_true(self):
        cfg = AppSettings(
            db_url="sqlite:///x.db",
            jina_api_key="k",
        )
        assert cfg.debug is True

    def test_service_name(self):
        cfg = AppSettings(
            db_url="sqlite:///x.db",
            jina_api_key="k",
        )
        assert cfg.service_name == "arxiv-sentinel"


class TestAppSettingsValidation:
    def test_rejects_invalid_db_url(self):
        with pytest.raises(ValueError):
            AppSettings(
                db_url="mysql://bad",
                jina_api_key="k",
            )

    def test_accepts_postgresql_url(self):
        cfg = AppSettings(
            db_url="postgresql://u:p@h/db",
            jina_api_key="k",
        )
        assert cfg.db_url.startswith("postgresql")

    def test_accepts_sqlite_url(self):
        cfg = AppSettings(
            db_url="sqlite:///test.db",
            jina_api_key="k",
        )
        assert cfg.db_url.startswith("sqlite")


class TestNestedConfigs:
    def test_search_defaults(self):
        cfg = AppSettings(
            db_url="sqlite:///x.db",
            jina_api_key="k",
        )
        assert cfg.search.vector_dim == 1024
        assert cfg.search.index == "arxiv-papers"

    def test_chunking_defaults(self):
        cfg = AppSettings(
            db_url="sqlite:///x.db",
            jina_api_key="k",
        )
        assert cfg.chunking.size == 600
        assert cfg.chunking.overlap == 100

    def test_cache_defaults(self):
        cfg = AppSettings(
            db_url="sqlite:///x.db",
            jina_api_key="k",
        )
        assert cfg.cache.ttl_hours == 6
        assert cfg.cache.port == 6379
