"""Tests for cache module."""

import json
from typing import Any
from unittest.mock import patch

from auraframes.cache import cache, save_to_cache


class TestSaveToCache:
    """Tests for save_to_cache function."""

    def test_save_to_cache_creates_file(self, tmp_path: Any) -> None:
        """save_to_cache should create a JSON file with data."""
        with patch("auraframes.cache.CACHE_DIR", str(tmp_path) + "/"):
            data = {"key": "value", "number": 42}
            save_to_cache("test_file", data)

            expected_path = tmp_path / "test_file.json"
            assert expected_path.exists()

            with open(expected_path) as f:
                loaded = json.load(f)
            assert loaded == data

    def test_save_to_cache_overwrites_existing(self, tmp_path: Any) -> None:
        """save_to_cache should overwrite existing file."""
        with patch("auraframes.cache.CACHE_DIR", str(tmp_path) + "/"):
            save_to_cache("test_file", {"old": "data"})
            save_to_cache("test_file", {"new": "data"})

            expected_path = tmp_path / "test_file.json"
            with open(expected_path) as f:
                loaded = json.load(f)
            assert loaded == {"new": "data"}


class TestCacheDecorator:
    """Tests for cache decorator."""

    def test_cache_stores_result(self, tmp_path: Any) -> None:
        """Cache decorator should store function result in file."""
        with patch("auraframes.cache.CACHE_DIR", str(tmp_path) + "/"):
            call_count = 0

            @cache("test_func")
            def expensive_function() -> dict[str, Any]:
                nonlocal call_count
                call_count += 1
                return {"result": "expensive computation"}

            # First call - should execute function
            result1 = expensive_function()
            assert result1 == {"result": "expensive computation"}
            assert call_count == 1

            # Second call - should use cache
            result2 = expensive_function()
            assert result2 == {"result": "expensive computation"}
            assert call_count == 1  # Function not called again

    def test_cache_with_use_arg(self, tmp_path: Any) -> None:
        """Cache decorator with use_arg should include argument in cache key."""
        with patch("auraframes.cache.CACHE_DIR", str(tmp_path) + "/"):
            call_count = 0

            @cache("test_func_arg", use_arg=True)
            def get_data(self: Any, key: str) -> dict[str, Any]:
                nonlocal call_count
                call_count += 1
                return {"key": key}

            # Call with different args
            result1 = get_data(None, "arg1")
            assert result1 == {"key": "arg1"}
            assert call_count == 1

            result2 = get_data(None, "arg2")
            assert result2 == {"key": "arg2"}
            assert call_count == 2

            # Call with same arg should use cache
            result3 = get_data(None, "arg1")
            assert result3 == {"key": "arg1"}
            assert call_count == 2  # Not called again

    def test_cache_reads_existing_file(self, tmp_path: Any) -> None:
        """Cache decorator should read from existing cache file."""
        with patch("auraframes.cache.CACHE_DIR", str(tmp_path) + "/"):
            # Pre-create cache file
            cache_path = tmp_path / "precached.json"
            with open(cache_path, "w") as f:
                json.dump({"cached": "value"}, f)

            call_count = 0

            @cache("precached")
            def should_not_run() -> dict[str, Any]:
                nonlocal call_count
                call_count += 1
                return {"new": "value"}

            result = should_not_run()
            assert result == {"cached": "value"}
            assert call_count == 0  # Function never called


class TestCacheEdgeCases:
    """Edge case tests for cache functionality."""

    def test_cache_with_list_data(self, tmp_path: Any) -> None:
        """Cache should handle list data correctly."""
        with patch("auraframes.cache.CACHE_DIR", str(tmp_path) + "/"):

            @cache("list_cache")
            def get_list() -> list[dict[str, Any]]:
                return [{"item": 1}, {"item": 2}]

            result = get_list()
            assert result == [{"item": 1}, {"item": 2}]

            # Verify file was created
            cache_path = tmp_path / "list_cache.json"
            assert cache_path.exists()

    def test_cache_with_nested_data(self, tmp_path: Any) -> None:
        """Cache should handle nested data structures."""
        with patch("auraframes.cache.CACHE_DIR", str(tmp_path) + "/"):

            @cache("nested_cache")
            def get_nested() -> dict[str, Any]:
                return {"level1": {"level2": {"level3": [1, 2, 3]}}}

            result = get_nested()
            assert result["level1"]["level2"]["level3"] == [1, 2, 3]

    def test_save_to_cache_handles_special_chars(self, tmp_path: Any) -> None:
        """save_to_cache should handle special characters in data."""
        with patch("auraframes.cache.CACHE_DIR", str(tmp_path) + "/"):
            data = {"text": "Special chars: '\"\n\t\\"}
            save_to_cache("special", data)

            expected_path = tmp_path / "special.json"
            with open(expected_path) as f:
                loaded = json.load(f)
            assert loaded == data
