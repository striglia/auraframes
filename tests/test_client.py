"""Tests for the HTTP client module."""

from typing import Any

from auraframes.client import _redact_sensitive


class TestRedactSensitive:
    """Tests for sensitive field redaction in logs."""

    def test_none_returns_none(self) -> None:
        assert _redact_sensitive(None) is None

    def test_empty_dict_returns_empty(self) -> None:
        assert _redact_sensitive({}) == {}

    def test_redacts_password_field(self) -> None:
        data = {"username": "alice", "password": "secret123"}
        result = _redact_sensitive(data)

        assert result == {"username": "alice", "password": "[REDACTED]"}

    def test_redacts_nested_password(self) -> None:
        """Matches actual login payload structure."""
        data: dict[str, Any] = {
            "user": {"email": "test@example.com", "password": "secret123"},
            "locale": "en-US",
        }
        result = _redact_sensitive(data)

        assert result == {
            "user": {"email": "test@example.com", "password": "[REDACTED]"},
            "locale": "en-US",
        }

    def test_preserves_non_sensitive_fields(self) -> None:
        data = {"email": "test@example.com", "name": "Alice"}
        result = _redact_sensitive(data)

        assert result == data
        assert result is not data  # Should be a copy

    def test_deeply_nested_password(self) -> None:
        data: dict[str, Any] = {
            "level1": {
                "level2": {
                    "password": "deep_secret",
                    "other": "value",
                }
            }
        }
        result = _redact_sensitive(data)

        assert result["level1"]["level2"]["password"] == "[REDACTED]"
        assert result["level1"]["level2"]["other"] == "value"

    def test_does_not_mutate_original(self) -> None:
        data: dict[str, Any] = {"user": {"password": "secret"}}
        _redact_sensitive(data)

        assert data["user"]["password"] == "secret"
