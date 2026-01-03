"""Tests for Aura orchestrator class."""

import re
from typing import Any
from unittest.mock import patch

import pytest
from pytest_httpx import HTTPXMock

from auraframes.aura import Aura


class TestAura:
    """Tests for the Aura orchestrator class."""

    def test_login_requires_email_and_password(self) -> None:
        """Login should raise ValueError when email or password is missing."""
        aura = Aura()

        with pytest.raises(ValueError, match="Email and password are required"):
            aura.login(email=None, password="pass")

        with pytest.raises(ValueError, match="Email and password are required"):
            aura.login(email="test@example.com", password=None)

    def test_login_success(
        self, httpx_mock: HTTPXMock, mock_user: dict[str, Any]
    ) -> None:
        """Login should authenticate and set headers."""
        httpx_mock.add_response(
            url="https://api.pushd.com/v5/login.json",
            method="POST",
            json={"result": {"current_user": mock_user}},
        )

        aura = Aura()
        result = aura.login(email="test@example.com", password="pass")

        assert result is aura  # Returns self for chaining
        assert (
            aura._client.http2_client.headers.get("x-token-auth")
            == mock_user["auth_token"]
        )

    def test_get_all_assets_single_page(
        self,
        httpx_mock: HTTPXMock,
        mock_user: dict[str, Any],
        mock_asset: dict[str, Any],
    ) -> None:
        """get_all_assets should return all assets from single page."""
        # Login first
        httpx_mock.add_response(
            url="https://api.pushd.com/v5/login.json",
            method="POST",
            json={"result": {"current_user": mock_user}},
        )

        # Assets response - single page (no cursor)
        httpx_mock.add_response(
            url=re.compile(r".*/frames/frame-456/assets\.json.*"),
            method="GET",
            json={"assets": [mock_asset], "next_page_cursor": None},
        )

        aura = Aura()
        aura.login(email="test@example.com", password="pass")

        assets = aura.get_all_assets("frame-456")

        assert len(assets) == 1
        assert assets[0].id == mock_asset["id"]

    @patch("time.sleep")  # Don't actually sleep in tests
    def test_get_all_assets_multiple_pages(
        self,
        mock_sleep: Any,
        httpx_mock: HTTPXMock,
        mock_user: dict[str, Any],
        mock_asset: dict[str, Any],
    ) -> None:
        """get_all_assets should paginate through all pages."""
        # Login first
        httpx_mock.add_response(
            url="https://api.pushd.com/v5/login.json",
            method="POST",
            json={"result": {"current_user": mock_user}},
        )

        # First page
        asset1 = mock_asset.copy()
        asset1["id"] = "asset-1"
        httpx_mock.add_response(
            url=re.compile(r".*/frames/frame-456/assets\.json.*"),
            method="GET",
            json={"assets": [asset1], "next_page_cursor": "page-2"},
        )

        # Second page
        asset2 = mock_asset.copy()
        asset2["id"] = "asset-2"
        httpx_mock.add_response(
            url=re.compile(r".*/frames/frame-456/assets\.json.*cursor=page-2.*"),
            method="GET",
            json={"assets": [asset2], "next_page_cursor": None},
        )

        aura = Aura()
        aura.login(email="test@example.com", password="pass")

        assets = aura.get_all_assets("frame-456")

        assert len(assets) == 2
        assert assets[0].id == "asset-1"
        assert assets[1].id == "asset-2"
        mock_sleep.assert_called()


class TestAuraLogin:
    """Additional login tests."""

    def test_login_returns_self_for_chaining(
        self, httpx_mock: HTTPXMock, mock_user: dict[str, Any]
    ) -> None:
        """Login should return self to enable method chaining."""
        httpx_mock.add_response(
            url="https://api.pushd.com/v5/login.json",
            method="POST",
            json={"result": {"current_user": mock_user}},
        )

        aura = Aura()
        result = aura.login(email="test@example.com", password="pass")

        assert result is aura
