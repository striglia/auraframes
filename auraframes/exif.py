import io
from fractions import Fraction
from typing import Any

import piexif
import piexif.helper
from geopy import Nominatim
from loguru import logger

from auraframes.models.asset import Asset

# Type alias for DMS tuple: (degrees, minutes, seconds, direction)
DmsTuple = tuple[tuple[int, int], tuple[int, int], tuple[int, int], str]
LocationDms = tuple[DmsTuple, DmsTuple]


# Most of the exif writing is from:
# https://gitlab.com/searchwing/development/payloads/ros-generic/-/blob/master/searchwing_common_py/scripts/ImageSaverNode.py


def build_gps_ifd(location_dms: LocationDms | None) -> dict[int, Any]:
    if not location_dms:
        return {}

    return {
        piexif.GPSIFD.GPSVersionID: (2, 3, 0, 0),
        piexif.GPSIFD.GPSLatitudeRef: location_dms[0][3],
        piexif.GPSIFD.GPSLatitude: location_dms[0][:-1],
        piexif.GPSIFD.GPSLongitudeRef: location_dms[1][3],
        piexif.GPSIFD.GPSLongitude: location_dms[1][:-1],
        piexif.GPSIFD.GPSAltitudeRef: 0,
        piexif.GPSIFD.GPSAltitude: (0, 1),
        piexif.GPSIFD.GPSStatus: b"A",
    }


class ExifWriter:
    geolocator = Nominatim(user_agent="Upload Scripting Test")
    cache: dict[str, LocationDms] = {}

    # TODO: LRU Cache would be nice but probably over-engineered
    def _lookup_gps(self, location_name: str) -> LocationDms | None:
        location_dms = self.cache.get(location_name)
        if location_dms:
            return location_dms

        try:
            location = self.geolocator.geocode(location_name)
        except Exception:
            logger.info(f"Failed to read GPS data for {location_name}")
            return None

        if not location:
            return None

        longitude_dms = convert_to_rational_dms(
            to_deg(location.longitude, is_longitude=True)
        )
        latitude_dms = convert_to_rational_dms(
            to_deg(location.latitude, is_longitude=False)
        )

        self.cache[location_name] = (longitude_dms, latitude_dms)
        return longitude_dms, latitude_dms

    def write_exif(
        self,
        image: bytes,
        asset: Asset,
        thumbnail: bytes | None = None,
        set_gps_ifd: bool = True,
    ) -> io.BytesIO:
        taken_datetime = asset.taken_at_dt.strftime("%Y:%m:%d %H:%M:%S").encode()

        exif_dict: dict[str, Any] = {
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: taken_datetime,
                piexif.ExifIFD.DateTimeDigitized: taken_datetime,
                piexif.ExifIFD.OffsetTime: b"-05:00",
                piexif.ExifIFD.OffsetTimeOriginal: b"-05:00",
            },
            "0th": {
                piexif.ImageIFD.DateTime: taken_datetime,
                piexif.ImageIFD.Artist: asset.user.name if asset.user else None,
            },
        }

        if set_gps_ifd and asset.location_name:
            location_dms = self._lookup_gps(asset.location_name)
            exif_dict["GPS"] = build_gps_ifd(location_dms)

        if thumbnail:
            exif_dict["thumbnail"] = thumbnail
            exif_dict["1st"] = {
                piexif.ImageIFD.Make: "Canon",
                piexif.ImageIFD.XResolution: (40, 1),
                piexif.ImageIFD.YResolution: (40, 1),
                piexif.ImageIFD.Software: "piexif",
            }
        new_imag = io.BytesIO()
        exif_bytes = piexif.dump(exif_dict)

        try:
            piexif.insert(exif_bytes, image, new_imag)
        except Exception:
            logger.info("Failed to write to image.")
        return new_imag


def change_to_rational(number: int | float) -> tuple[int, int]:
    f = Fraction(str(number))
    return f.numerator, f.denominator


def convert_to_rational_dms(dms: tuple[int, int, float, str]) -> DmsTuple:
    return (
        change_to_rational(dms[0]),
        change_to_rational(dms[1]),
        change_to_rational(dms[2]),
        dms[3],
    )


def clone_exif(original_path: str, clone_path: str) -> None:
    piexif.transplant(original_path, clone_path)


def get_readable_exif(image_path: str) -> dict[str, dict[str, Any]]:
    exif_dict = piexif.load(image_path)
    readable_dict: dict[str, dict[str, Any]] = {}
    for ifd in exif_dict:
        readable_dict[ifd] = {}
        if not exif_dict[ifd]:
            continue
        for tag in exif_dict[ifd]:
            if ifd != "thumbnail":
                readable_dict[ifd][piexif.TAGS[ifd][tag]["name"]] = exif_dict[ifd][tag]
            else:
                readable_dict[ifd][tag] = exif_dict[ifd][tag]
    return readable_dict


def to_deg(value: float, is_longitude: bool) -> tuple[int, int, float, str]:
    # convert decimal coordinates into degrees, minutes and seconds tuple
    # Keyword arguments:
    #   value is float gps-value,
    #   loc is direction list ["S", "N"] or ["W", "E"]
    # return: tuple like (25, 13, 48.343 ,'N')
    loc = ["W", "E"] if is_longitude else ["S", "N"]

    if value < 0:
        loc_value = loc[0]
    elif value > 0:
        loc_value = loc[1]
    else:
        loc_value = ""
    abs_value = abs(value)
    deg = int(abs_value)
    t1 = (abs_value - deg) * 60
    min = int(t1)
    sec = round((t1 - min) * 60, 5)
    return deg, min, sec, loc_value
