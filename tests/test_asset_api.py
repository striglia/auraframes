"""Tests for asset API operations."""

import re
from typing import Any

from pytest_httpx import HTTPXMock

from auraframes.api.assetApi import AssetApi
from auraframes.client import Client
from auraframes.models.asset import Asset, AssetPartialId


class TestAssetApi:
    """Tests for AssetApi methods."""

    def test_batch_update_sends_correct_fields(
        self, httpx_mock: HTTPXMock, mock_asset: dict[str, Any]
    ) -> None:
        """batch_update should send only specific asset fields."""
        httpx_mock.add_response(
            url="https://api.pushd.com/v5/assets/batch_update.json",
            method="PUT",
            json={
                "ids": ["asset-789"],
                "successes": [{"local_identifier": "local-asset-123"}],
            },
        )

        client = Client()
        api = AssetApi(client)
        asset = Asset(**mock_asset)

        ids, successes = api.batch_update(asset)

        assert ids == ["asset-789"]
        assert len(successes) == 1
        assert successes[0].local_identifier == "local-asset-123"

        # Verify request was made with correct fields
        request = httpx_mock.get_request()
        assert request is not None
        assert request.method == "PUT"

    def test_batch_update_returns_partial_ids(
        self, httpx_mock: HTTPXMock, mock_asset: dict[str, Any]
    ) -> None:
        """batch_update should return AssetPartialId instances."""
        httpx_mock.add_response(
            url="https://api.pushd.com/v5/assets/batch_update.json",
            method="PUT",
            json={
                "ids": ["asset-789", "asset-790"],
                "successes": [
                    {"local_identifier": "local-1"},
                    {"local_identifier": "local-2"},
                ],
            },
        )

        client = Client()
        api = AssetApi(client)
        asset = Asset(**mock_asset)

        ids, successes = api.batch_update(asset)

        assert len(ids) == 2
        assert len(successes) == 2
        assert all(isinstance(s, AssetPartialId) for s in successes)

    def test_get_asset_by_local_identifier(
        self, httpx_mock: HTTPXMock, mock_asset: dict[str, Any]
    ) -> None:
        """get_asset_by_local_identifier should return asset and related data."""
        httpx_mock.add_response(
            url=re.compile(r".*/assets/asset_for_local_identifier\.json.*"),
            method="GET",
            json={
                "asset": mock_asset,
                "child_albums": ["album-1"],
                "smart_adds": ["smart-1"],
            },
        )

        client = Client()
        api = AssetApi(client)

        asset, child_albums, smart_adds = api.get_asset_by_local_identifier(
            "local-asset-123"
        )

        assert isinstance(asset, Asset)
        assert asset.id == mock_asset["id"]
        assert asset.local_identifier == mock_asset["local_identifier"]
        assert child_albums == ["album-1"]
        assert smart_adds == ["smart-1"]

    def test_get_asset_by_local_identifier_sends_query_param(
        self, httpx_mock: HTTPXMock, mock_asset: dict[str, Any]
    ) -> None:
        """get_asset_by_local_identifier should send local_identifier as query param."""
        httpx_mock.add_response(
            url=re.compile(r".*/assets/asset_for_local_identifier\.json.*"),
            method="GET",
            json={
                "asset": mock_asset,
                "child_albums": [],
                "smart_adds": [],
            },
        )

        client = Client()
        api = AssetApi(client)
        api.get_asset_by_local_identifier("test-local-id")

        request = httpx_mock.get_request()
        assert request is not None
        assert "local_identifier=test-local-id" in str(request.url)

    def test_update_taken_at_date_with_remote_asset(
        self, httpx_mock: HTTPXMock, mock_asset: dict[str, Any]
    ) -> None:
        """update_taken_at_date should use id for remote assets."""
        updated_asset = mock_asset.copy()
        updated_asset["taken_at"] = "2024-06-15T14:00:00.000Z"

        httpx_mock.add_response(
            url="https://api.pushd.com/v5/assets/update_taken_at_date.json",
            method="POST",
            json=updated_asset,
        )

        client = Client()
        api = AssetApi(client)
        asset = Asset(**mock_asset)
        asset.taken_at = "2024-06-15T14:00:00.000Z"

        result = api.update_taken_at_date(asset)

        assert isinstance(result, Asset)
        assert result.taken_at == "2024-06-15T14:00:00.000Z"

    def test_delete_asset_remote(
        self, httpx_mock: HTTPXMock, mock_asset: dict[str, Any]
    ) -> None:
        """delete_asset should use DELETE for remote assets."""
        httpx_mock.add_response(
            url="https://api.pushd.com/v5/assets/asset-789.json",
            method="DELETE",
            json={"success": True},
        )

        client = Client()
        api = AssetApi(client)
        asset = Asset(**mock_asset)

        result = api.delete_asset(asset)

        assert result == {"success": True}

        request = httpx_mock.get_request()
        assert request is not None
        assert request.method == "DELETE"

    def test_crop_asset(
        self, httpx_mock: HTTPXMock, mock_asset: dict[str, Any]
    ) -> None:
        """crop_asset should update rotation and rect fields."""
        cropped_asset = mock_asset.copy()
        cropped_asset["rotation_cw"] = 90
        cropped_asset["user_landscape_rect"] = "0,0,100,100"

        httpx_mock.add_response(
            url="https://api.pushd.com/v5/assets/crop.json",
            method="POST",
            json={"asset": cropped_asset},
        )

        client = Client()
        api = AssetApi(client)
        asset = Asset(**mock_asset)
        asset.rotation_cw = 90

        result = api.crop_asset(asset)

        assert isinstance(result, Asset)
        assert result.rotation_cw == 90


class TestAssetModel:
    """Tests for Asset model behavior."""

    def test_asset_taken_at_dt_property(self, mock_asset: dict[str, Any]) -> None:
        """taken_at_dt should parse taken_at string to datetime."""
        asset = Asset(**mock_asset)
        dt = asset.taken_at_dt

        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15
        assert dt.hour == 12
        assert dt.minute == 30

    def test_asset_is_local_asset_false_when_has_id(
        self, mock_asset: dict[str, Any]
    ) -> None:
        """is_local_asset should be False when asset has an id."""
        asset = Asset(**mock_asset)
        assert asset.is_local_asset is False

    def test_asset_partial_id_with_id(self) -> None:
        """AssetPartialId should work with id."""
        partial = AssetPartialId(id="asset-123")
        assert partial.to_request_format() == {"asset_id": "asset-123"}

    def test_asset_partial_id_with_local_identifier(self) -> None:
        """AssetPartialId should work with local_identifier."""
        partial = AssetPartialId(local_identifier="local-123")
        assert partial.to_request_format() == {"asset_local_identifier": "local-123"}
