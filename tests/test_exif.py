"""Tests for exif module."""

from io import BytesIO
from typing import Any
from unittest.mock import MagicMock, patch

from PIL import Image

from auraframes.exif import (
    ExifWriter,
    build_gps_ifd,
    change_to_rational,
    convert_to_rational_dms,
    to_deg,
)
from auraframes.models.asset import Asset


class TestToDeg:
    """Tests for to_deg conversion function."""

    def test_positive_latitude(self) -> None:
        """Should convert positive latitude to DMS with N direction."""
        deg, min, sec, direction = to_deg(40.7128, is_longitude=False)
        assert deg == 40
        assert min == 42
        assert direction == "N"

    def test_negative_latitude(self) -> None:
        """Should convert negative latitude to DMS with S direction."""
        deg, min, sec, direction = to_deg(-34.6037, is_longitude=False)
        assert deg == 34
        assert min == 36
        assert direction == "S"

    def test_positive_longitude(self) -> None:
        """Should convert positive longitude to DMS with E direction."""
        deg, min, sec, direction = to_deg(139.6917, is_longitude=True)
        assert deg == 139
        assert min == 41
        assert direction == "E"

    def test_negative_longitude(self) -> None:
        """Should convert negative longitude to DMS with W direction."""
        deg, min, sec, direction = to_deg(-74.0060, is_longitude=True)
        assert deg == 74
        assert min == 0
        assert direction == "W"

    def test_zero_value(self) -> None:
        """Should handle zero value with empty direction."""
        deg, min, sec, direction = to_deg(0.0, is_longitude=True)
        assert deg == 0
        assert min == 0
        assert sec == 0.0
        assert direction == ""


class TestChangeToRational:
    """Tests for change_to_rational function."""

    def test_integer_value(self) -> None:
        """Should convert integer to rational tuple."""
        result = change_to_rational(42)
        assert result == (42, 1)

    def test_simple_fraction(self) -> None:
        """Should convert simple decimal to rational."""
        result = change_to_rational(0.5)
        assert result == (1, 2)

    def test_float_value(self) -> None:
        """Should convert float to rational tuple."""
        result = change_to_rational(3.14159)
        num, den = result
        assert isinstance(num, int)
        assert isinstance(den, int)
        # Verify it's approximately correct
        assert abs(num / den - 3.14159) < 0.0001


class TestConvertToRationalDms:
    """Tests for convert_to_rational_dms function."""

    def test_converts_dms_tuple(self) -> None:
        """Should convert DMS tuple to rational format."""
        dms = (40, 42, 46.08, "N")
        result = convert_to_rational_dms(dms)

        assert len(result) == 4
        assert result[0] == (40, 1)  # degrees
        assert result[1] == (42, 1)  # minutes
        assert isinstance(result[2], tuple)  # seconds as rational
        assert result[3] == "N"  # direction


class TestBuildGpsIfd:
    """Tests for build_gps_ifd function."""

    def test_returns_empty_dict_when_no_location(self) -> None:
        """Should return empty dict when location_dms is None."""
        result = build_gps_ifd(None)
        assert result == {}

    def test_returns_gps_dict_with_location(self) -> None:
        """Should return GPS IFD dict with valid location."""
        # DMS tuples for lat/long
        lat_dms = ((40, 1), (42, 1), (46, 1), "N")
        long_dms = ((74, 1), (0, 1), (21, 1), "W")
        location_dms = (lat_dms, long_dms)

        result = build_gps_ifd(location_dms)

        assert len(result) > 0
        # Check key GPS fields are present (using piexif constants)
        # GPSVersionID, GPSLatitudeRef, GPSLatitude, etc.


class TestExifWriter:
    """Tests for ExifWriter class."""

    def test_write_exif_returns_bytesio(self, mock_asset: dict[str, Any]) -> None:
        """write_exif should return a BytesIO object."""
        # Create a minimal valid JPEG image
        img = Image.new("RGB", (100, 100), color="red")
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        image_data = img_bytes.getvalue()

        asset = Asset(**mock_asset)
        asset.location_name = None  # Avoid geocoding

        writer = ExifWriter()
        result = writer.write_exif(image_data, asset, set_gps_ifd=False)

        assert isinstance(result, BytesIO)

    @patch.object(ExifWriter, "_lookup_gps")
    def test_write_exif_skips_gps_when_no_location(
        self, mock_lookup: MagicMock, mock_asset: dict[str, Any]
    ) -> None:
        """write_exif should skip GPS lookup when location_name is None."""
        img = Image.new("RGB", (100, 100), color="blue")
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        image_data = img_bytes.getvalue()

        mock_asset["location_name"] = None
        asset = Asset(**mock_asset)

        writer = ExifWriter()
        writer.write_exif(image_data, asset)

        mock_lookup.assert_not_called()

    @patch.object(ExifWriter, "_lookup_gps")
    def test_write_exif_includes_thumbnail(
        self, mock_lookup: MagicMock, mock_asset: dict[str, Any]
    ) -> None:
        """write_exif should include thumbnail when provided."""
        mock_lookup.return_value = None

        # Create main image
        img = Image.new("RGB", (100, 100), color="green")
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        image_data = img_bytes.getvalue()

        # Create thumbnail
        thumb = Image.new("RGB", (50, 50), color="yellow")
        thumb_bytes = BytesIO()
        thumb.save(thumb_bytes, format="JPEG")
        thumbnail_data = thumb_bytes.getvalue()

        mock_asset["location_name"] = None
        asset = Asset(**mock_asset)

        writer = ExifWriter()
        result = writer.write_exif(image_data, asset, thumbnail=thumbnail_data)

        assert isinstance(result, BytesIO)


class TestExifWriterGpsLookup:
    """Tests for GPS lookup functionality."""

    def test_lookup_gps_uses_cache(self) -> None:
        """_lookup_gps should use cached results."""
        writer = ExifWriter()

        # Pre-populate cache
        mock_dms = (
            ((40, 1), (42, 1), (46, 1), "N"),
            ((74, 1), (0, 1), (21, 1), "W"),
        )
        writer.cache["New York"] = mock_dms

        result = writer._lookup_gps("New York")
        assert result == mock_dms

    @patch("auraframes.exif.Nominatim")
    def test_lookup_gps_handles_geocoder_failure(
        self, mock_nominatim_class: MagicMock
    ) -> None:
        """_lookup_gps should return None when geocoder fails."""
        mock_geolocator = MagicMock()
        mock_geolocator.geocode.side_effect = Exception("Network error")
        mock_nominatim_class.return_value = mock_geolocator

        writer = ExifWriter()
        writer.geolocator = mock_geolocator

        result = writer._lookup_gps("Unknown Place")
        assert result is None

    @patch("auraframes.exif.Nominatim")
    def test_lookup_gps_returns_none_for_unknown_location(
        self, mock_nominatim_class: MagicMock
    ) -> None:
        """_lookup_gps should return None when location not found."""
        mock_geolocator = MagicMock()
        mock_geolocator.geocode.return_value = None
        mock_nominatim_class.return_value = mock_geolocator

        writer = ExifWriter()
        writer.geolocator = mock_geolocator

        result = writer._lookup_gps("Nonexistent Location 12345")
        assert result is None
