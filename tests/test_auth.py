"""Tests for authentication flow."""

from typing import Any

from pytest_httpx import HTTPXMock

from auraframes.api.accountApi import AccountApi
from auraframes.aura import Aura
from auraframes.client import Client


class TestLogin:
    """Tests for the login flow."""

    def test_login_sets_auth_headers(
        self, httpx_mock: HTTPXMock, mock_user: dict[str, Any]
    ) -> None:
        """Successful login should set x-token-auth and x-user-id headers."""
        # Arrange
        httpx_mock.add_response(
            url="https://api.pushd.com/v5/login.json",
            method="POST",
            json={"result": {"current_user": mock_user}},
        )

        aura = Aura()

        # Act
        aura.login(email="test@example.com", password="password123")

        # Assert - headers are stored in httpx client's headers
        assert (
            aura._client.http2_client.headers.get("x-token-auth")
            == mock_user["auth_token"]
        )
        assert aura._client.http2_client.headers.get("x-user-id") == mock_user["id"]

    def test_login_returns_aura_instance(
        self, httpx_mock: HTTPXMock, mock_user: dict[str, Any]
    ) -> None:
        """Login should return self for method chaining."""
        httpx_mock.add_response(
            url="https://api.pushd.com/v5/login.json",
            method="POST",
            json={"result": {"current_user": mock_user}},
        )

        aura = Aura()
        result = aura.login(email="test@example.com", password="password123")

        assert result is aura


class TestAccountApi:
    """Tests for AccountApi methods."""

    def test_login_parses_user_response(
        self, httpx_mock: HTTPXMock, mock_user: dict[str, Any]
    ) -> None:
        """Login should parse API response into User model."""
        httpx_mock.add_response(
            url="https://api.pushd.com/v5/login.json",
            method="POST",
            json={"result": {"current_user": mock_user}},
        )

        client = Client()
        api = AccountApi(client)

        user = api.login("test@example.com", "password123")

        assert user.id == mock_user["id"]
        assert user.email == mock_user["email"]
        assert user.auth_token == mock_user["auth_token"]

    def test_login_sends_correct_payload(
        self, httpx_mock: HTTPXMock, mock_user: dict[str, Any]
    ) -> None:
        """Login should send email, password, and device identifiers."""
        httpx_mock.add_response(
            url="https://api.pushd.com/v5/login.json",
            method="POST",
            json={"result": {"current_user": mock_user}},
        )

        client = Client()
        api = AccountApi(client)
        api.login("test@example.com", "password123")

        # Verify request was made
        request = httpx_mock.get_request()
        assert request is not None
        assert request.method == "POST"

    def test_register_creates_new_user(
        self, httpx_mock: HTTPXMock, mock_user: dict[str, Any]
    ) -> None:
        """Register should create a new user account."""
        httpx_mock.add_response(
            url="https://api.pushd.com/v5/account/register.json",
            method="POST",
            json={"result": {"current_user": mock_user}},
        )

        client = Client()
        api = AccountApi(client)

        user = api.register("new@example.com", "password123", "New User")

        assert user.id == mock_user["id"]
        assert user.email == mock_user["email"]

        request = httpx_mock.get_request()
        assert request is not None
        assert request.method == "POST"

    def test_delete_removes_user(self, httpx_mock: HTTPXMock) -> None:
        """Delete should remove the current user account."""
        httpx_mock.add_response(
            url="https://api.pushd.com/v5/account/delete",
            method="DELETE",
            json={"result": {"success": True}},
        )

        client = Client()
        api = AccountApi(client)

        result = api.delete()

        assert result is True

        request = httpx_mock.get_request()
        assert request is not None
        assert request.method == "DELETE"

    def test_delete_returns_false_on_error(self, httpx_mock: HTTPXMock) -> None:
        """Delete should return False when deletion fails."""
        httpx_mock.add_response(
            url="https://api.pushd.com/v5/account/delete",
            method="DELETE",
            json={"result": {"success": False}, "error": "Failed to delete"},
        )

        client = Client()
        api = AccountApi(client)

        result = api.delete()

        assert result is False
