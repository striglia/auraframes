"""Tests for frame API operations."""

import re
from typing import Any

from pytest_httpx import HTTPXMock

from auraframes.api.frameApi import FrameApi
from auraframes.client import Client
from auraframes.models.activity import Activity
from auraframes.models.asset import Asset, AssetPartialId
from auraframes.models.frame import Frame, FramePartial


class TestFrameApi:
    """Tests for FrameApi methods."""

    def test_get_frames_returns_frame_list(
        self, httpx_mock: HTTPXMock, mock_frame: dict[str, Any]
    ) -> None:
        """get_frames should return a list of Frame models."""
        httpx_mock.add_response(
            url="https://api.pushd.com/v5/frames.json",
            method="GET",
            json={"frames": [mock_frame]},
        )

        client = Client()
        api = FrameApi(client)

        frames = api.get_frames()

        assert len(frames) == 1
        assert isinstance(frames[0], Frame)
        assert frames[0].id == mock_frame["id"]
        assert frames[0].name == mock_frame["name"]

    def test_get_frame_by_id(
        self, httpx_mock: HTTPXMock, mock_frame: dict[str, Any]
    ) -> None:
        """get_frame should return a single Frame by ID."""
        frame_id = mock_frame["id"]
        httpx_mock.add_response(
            url=f"https://api.pushd.com/v5/frames/{frame_id}.json",
            method="GET",
            json={"frame": mock_frame, "total_asset_count": 100},
        )

        client = Client()
        api = FrameApi(client)

        frame, _ = api.get_frame(frame_id)

        assert isinstance(frame, Frame)
        assert frame.id == frame_id
        assert frame.name == mock_frame["name"]

    def test_get_assets_returns_asset_list(
        self,
        httpx_mock: HTTPXMock,
        mock_frame: dict[str, Any],
        mock_asset: dict[str, Any],
    ) -> None:
        """get_assets should return a list of Asset models with pagination cursor."""
        frame_id = mock_frame["id"]
        httpx_mock.add_response(
            url=re.compile(rf".*/frames/{frame_id}/assets\.json.*"),
            method="GET",
            json={
                "assets": [mock_asset],
                "next_page_cursor": "cursor-abc123",
            },
        )

        client = Client()
        api = FrameApi(client)

        assets, cursor = api.get_assets(frame_id)

        assert len(assets) == 1
        assert isinstance(assets[0], Asset)
        assert assets[0].id == mock_asset["id"]
        assert cursor == "cursor-abc123"

    def test_get_assets_with_cursor(
        self,
        httpx_mock: HTTPXMock,
        mock_frame: dict[str, Any],
        mock_asset: dict[str, Any],
    ) -> None:
        """get_assets should pass cursor for pagination."""
        frame_id = mock_frame["id"]
        httpx_mock.add_response(
            url=re.compile(rf".*/frames/{frame_id}/assets\.json.*"),
            method="GET",
            json={"assets": [mock_asset], "next_page_cursor": None},
        )

        client = Client()
        api = FrameApi(client)

        assets, cursor = api.get_assets(frame_id, cursor="prev-cursor")

        assert len(assets) == 1
        assert cursor is None

        request = httpx_mock.get_request()
        assert request is not None
        assert "cursor=prev-cursor" in str(request.url)

    def test_get_activities_returns_activity_list(
        self,
        httpx_mock: HTTPXMock,
        mock_frame: dict[str, Any],
        mock_activity: dict[str, Any],
    ) -> None:
        """get_activities should return a list of Activity models."""
        frame_id = mock_frame["id"]
        httpx_mock.add_response(
            url=re.compile(rf".*/frames/{frame_id}/activities\.json.*"),
            method="GET",
            json={
                "activities": [mock_activity],
                "next_page_cursor": None,
            },
        )

        client = Client()
        api = FrameApi(client)

        activities, cursor = api.get_activities(frame_id)

        assert len(activities) == 1
        assert isinstance(activities[0], Activity)
        assert activities[0].id == mock_activity["id"]
        assert cursor is None

    def test_show_asset(
        self, httpx_mock: HTTPXMock, mock_frame: dict[str, Any]
    ) -> None:
        """show_asset should request frame to display specific asset."""
        frame_id = mock_frame["id"]
        httpx_mock.add_response(
            url=f"https://api.pushd.com/v5/frames/{frame_id}/goto.json",
            method="POST",
            json={"showing": True},
        )

        client = Client()
        api = FrameApi(client)

        result = api.show_asset(frame_id, "asset-123", "2024-01-01T12:00:00.000Z")

        assert result is True

    def test_show_asset_returns_false_when_not_showing(
        self, httpx_mock: HTTPXMock, mock_frame: dict[str, Any]
    ) -> None:
        """show_asset should return False when frame cannot show asset."""
        frame_id = mock_frame["id"]
        httpx_mock.add_response(
            url=f"https://api.pushd.com/v5/frames/{frame_id}/goto.json",
            method="POST",
            json={"showing": False},
        )

        client = Client()
        api = FrameApi(client)

        # Empty string triggers auto-generation of goto_time
        result = api.show_asset(frame_id, "asset-123", "")

        assert result is False

    def test_update_frame(
        self, httpx_mock: HTTPXMock, mock_frame: dict[str, Any]
    ) -> None:
        """update_frame should update frame properties."""
        frame_id = mock_frame["id"]
        updated_frame = mock_frame.copy()
        updated_frame["name"] = "Updated Name"

        httpx_mock.add_response(
            url=f"https://api.pushd.com/v5/frames/{frame_id}.json",
            method="PUT",
            json={"frame": updated_frame},
        )

        client = Client()
        api = FrameApi(client)

        # FramePartial uses AllOptional metaclass to make all fields optional
        frame_partial = FramePartial(name="Updated Name")  # type: ignore[call-arg]
        result = api.update_frame(frame_id, frame_partial)

        assert isinstance(result, Frame)
        assert result.name == "Updated Name"

    def test_select_asset(
        self, httpx_mock: HTTPXMock, mock_frame: dict[str, Any]
    ) -> None:
        """select_asset should associate asset with frame."""
        frame_id = mock_frame["id"]
        httpx_mock.add_response(
            url=f"https://api.pushd.com/v5/frames/{frame_id}/select_asset.json",
            method="POST",
            json={"number_failed": 0},
        )

        client = Client()
        api = FrameApi(client)

        asset_partial = AssetPartialId(local_identifier="local-123")
        result = api.select_asset(frame_id, asset_partial)

        assert result == 0

    def test_exclude_asset(
        self, httpx_mock: HTTPXMock, mock_frame: dict[str, Any]
    ) -> None:
        """exclude_asset should exclude asset from slideshow."""
        frame_id = mock_frame["id"]
        httpx_mock.add_response(
            url=f"https://api.pushd.com/v5/frames/{frame_id}/exclude_asset",
            method="POST",
            json={"number_failed": 0},
        )

        client = Client()
        api = FrameApi(client)

        asset_partial = AssetPartialId(id="asset-123")
        result = api.exclude_asset(frame_id, asset_partial)

        assert result == 0

    def test_remove_asset(
        self, httpx_mock: HTTPXMock, mock_frame: dict[str, Any]
    ) -> None:
        """remove_asset should disassociate asset from frame."""
        frame_id = mock_frame["id"]
        httpx_mock.add_response(
            url=f"https://api.pushd.com/v5/frames/{frame_id}/remove_asset.json",
            method="POST",
            json={"number_failed": 0},
        )

        client = Client()
        api = FrameApi(client)

        asset_partial = AssetPartialId(id="asset-123")
        result = api.remove_asset(frame_id, asset_partial)

        assert result == 0

    def test_reconfigure(
        self, httpx_mock: HTTPXMock, mock_frame: dict[str, Any]
    ) -> None:
        """reconfigure should call the reconfigure endpoint."""
        frame_id = mock_frame["id"]
        httpx_mock.add_response(
            url=f"https://api.pushd.com/v5/frames/{frame_id}/reconfigure.json",
            method="POST",
            json={"success": True},
        )

        client = Client()
        api = FrameApi(client)

        result = api.reconfigure(frame_id)

        assert result == {"success": True}


class TestFrameModel:
    """Tests for Frame model behavior."""

    def test_is_portrait_orientation_2(self, mock_frame: dict[str, Any]) -> None:
        """Orientation 2 should be portrait."""
        mock_frame["orientation"] = 2
        frame = Frame(**mock_frame)
        assert frame.is_portrait() is True

    def test_is_portrait_orientation_3(self, mock_frame: dict[str, Any]) -> None:
        """Orientation 3 should be portrait."""
        mock_frame["orientation"] = 3
        frame = Frame(**mock_frame)
        assert frame.is_portrait() is True

    def test_is_landscape_orientation_1(self, mock_frame: dict[str, Any]) -> None:
        """Orientation 1 should be landscape."""
        mock_frame["orientation"] = 1
        frame = Frame(**mock_frame)
        assert frame.is_portrait() is False

    def test_get_frame_type_default(self, mock_frame: dict[str, Any]) -> None:
        """Frame type should default to 'normal' when None."""
        mock_frame["frame_type"] = None
        frame = Frame(**mock_frame)
        assert frame.get_frame_type() == "normal"

    def test_frame_model_validates_required_fields(
        self, mock_frame: dict[str, Any]
    ) -> None:
        """Frame model should validate all required fields are present."""
        frame = Frame(**mock_frame)
        assert frame.id is not None
        assert frame.name is not None
        assert frame.user_id is not None
