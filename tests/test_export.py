"""Tests for export module."""

import os
from datetime import datetime
from io import BytesIO
from typing import Any

from PIL import Image
from pytest_httpx import HTTPXMock

from auraframes.export import (
    _get_path_safe_datetime,
    get_image_from_asset,
    get_thumbnail,
)
from auraframes.models.asset import Asset


class TestGetPathSafeDatetime:
    """Tests for _get_path_safe_datetime function."""

    def test_formats_datetime_correctly(self) -> None:
        """Should format datetime as YYYYMMDDTHHMMSS."""
        dt = datetime(2024, 1, 15, 14, 30, 45)
        result = _get_path_safe_datetime(dt)
        assert result == "20240115T143045"

    def test_handles_midnight(self) -> None:
        """Should handle midnight correctly."""
        dt = datetime(2024, 12, 31, 0, 0, 0)
        result = _get_path_safe_datetime(dt)
        assert result == "20241231T000000"

    def test_handles_single_digit_values(self) -> None:
        """Should pad single digit values with zeros."""
        dt = datetime(2024, 1, 1, 1, 1, 1)
        result = _get_path_safe_datetime(dt)
        assert result == "20240101T010101"


class TestGetThumbnail:
    """Tests for get_thumbnail function."""

    def test_returns_none_when_no_thumbnail_url(
        self, mock_asset: dict[str, Any]
    ) -> None:
        """Should return None when asset has no thumbnail_url."""
        mock_asset["thumbnail_url"] = None
        asset = Asset(**mock_asset)

        result = get_thumbnail(asset)
        assert result is None

    def test_returns_thumbnail_bytes_on_valid_image(
        self, httpx_mock: HTTPXMock, mock_asset: dict[str, Any]
    ) -> None:
        """Should return thumbnail bytes when image is valid."""
        # Create a valid test image
        img = Image.new("RGB", (100, 100), color="red")
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)

        httpx_mock.add_response(
            url=mock_asset["thumbnail_url"],
            method="GET",
            content=img_bytes.getvalue(),
        )

        asset = Asset(**mock_asset)
        result = get_thumbnail(asset)

        assert result is not None
        assert len(result) > 0

    def test_generates_thumbnail_from_original_on_invalid_http_thumbnail(
        self, httpx_mock: HTTPXMock, mock_asset: dict[str, Any]
    ) -> None:
        """Should generate thumbnail from original when HTTP thumbnail is invalid."""
        # Return invalid image data from HTTP
        httpx_mock.add_response(
            url=mock_asset["thumbnail_url"],
            method="GET",
            content=b"not an image",
        )

        # Create a valid original image
        original_img = Image.new("RGB", (500, 500), color="blue")
        original_bytes = BytesIO()
        original_img.save(original_bytes, format="JPEG")
        original_bytes.seek(0)

        asset = Asset(**mock_asset)
        result = get_thumbnail(asset, original_image=original_bytes)

        assert result is not None
        assert len(result) > 0


class TestGetImageFromAsset:
    """Tests for get_image_from_asset function."""

    def test_fetches_image_from_proxy(
        self, httpx_mock: HTTPXMock, mock_asset: dict[str, Any], tmp_path: Any
    ) -> None:
        """Should fetch image from imgproxy URL."""
        # Create a test image
        img = Image.new("RGB", (100, 100), color="green")
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        test_image_data = img_bytes.getvalue()

        # Mock the image proxy request
        user_id = mock_asset["user_id"]
        file_name = mock_asset["file_name"]
        httpx_mock.add_response(
            url=f"https://imgproxy.pushd.com/{user_id}/{file_name}",
            method="GET",
            content=test_image_data,
        )

        asset = Asset(**mock_asset)
        result = get_image_from_asset(asset, str(tmp_path) + "/")

        assert result == test_image_data

    def test_uses_cache_when_file_exists(
        self, mock_asset: dict[str, Any], tmp_path: Any
    ) -> None:
        """Should return cached file when it exists."""
        asset = Asset(**mock_asset)

        # Pre-create the cached file
        expected_filename = (
            f"{tmp_path}/{_get_path_safe_datetime(asset.taken_at_dt)}-{asset.file_name}"
        )
        os.makedirs(os.path.dirname(expected_filename), exist_ok=True)
        cached_content = b"cached image content"
        with open(expected_filename, "wb") as f:
            f.write(cached_content)

        # Should return cached content without making HTTP request
        result = get_image_from_asset(asset, str(tmp_path) + "/")
        assert result == cached_content

    def test_ignores_cache_when_flag_set(
        self, httpx_mock: HTTPXMock, mock_asset: dict[str, Any], tmp_path: Any
    ) -> None:
        """Should fetch fresh image when ignore_cache is True."""
        asset = Asset(**mock_asset)

        # Pre-create cached file
        expected_filename = (
            f"{tmp_path}/{_get_path_safe_datetime(asset.taken_at_dt)}-{asset.file_name}"
        )
        os.makedirs(os.path.dirname(expected_filename), exist_ok=True)
        with open(expected_filename, "wb") as f:
            f.write(b"old cached content")

        # Mock fresh image response
        fresh_content = b"fresh image content"
        user_id = mock_asset["user_id"]
        file_name = mock_asset["file_name"]
        httpx_mock.add_response(
            url=f"https://imgproxy.pushd.com/{user_id}/{file_name}",
            method="GET",
            content=fresh_content,
        )

        result = get_image_from_asset(asset, str(tmp_path) + "/", ignore_cache=True)
        assert result == fresh_content
