"""Tests for frame API operations."""

from typing import Any

from pytest_httpx import HTTPXMock

from auraframes.api.frameApi import FrameApi
from auraframes.client import Client
from auraframes.models.frame import Frame


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
