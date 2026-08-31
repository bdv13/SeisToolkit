from functools import lru_cache
from math import floor
from typing import SupportsFloat

from pyproj import CRS, Transformer


def get_utm_zone(lat: float, lon: float) -> str:
    """Return UTM zone (e.g. '35N') for WGS84 coordinates"""
    if lat is None or lon is None:
        raise ValueError("lat/lon cannot be None")

    if not -80 <= lat <= 84:
        raise ValueError("UTM is defined only between 80°S and 84°N.")

    if not -180 <= lon <= 180:
        raise ValueError("Longitude must be in range [-180, 180].")

    zone = floor((lon + 180) / 6) + 1
    hemisphere = "N" if lat >= 0 else "S"

    return f"{zone}{hemisphere}"


@lru_cache(maxsize=64)
def _get_transformer_inverse(zone_number: int, south: bool) -> Transformer:
    """Return a cached inverse coordinate transformer for UTM to WGS84."""
    epsg = 32700 + zone_number if south else 32600 + zone_number

    return Transformer.from_crs(
        epsg,
        4326,
        always_xy=True,
    )


def utm_to_wgs84(x: float, y: float, zone: str) -> tuple[float, float]:
    """Convert UTM coordinates to WGS84 (lat, lon - DD.DDDDDD)."""
    if len(zone) < 2:
        raise ValueError(f"Invalid UTM zone: {zone!r}")

    zone_number = int(zone[:-1])
    hemisphere = zone[-1].upper()

    if hemisphere not in ("N", "S"):
        raise ValueError(f"Zone must end with N or S, got: {zone!r}")

    south = hemisphere == "S"

    transformer = _get_transformer_inverse(zone_number, south)

    lon, lat = transformer.transform(x, y)

    return lat, lon


@lru_cache(maxsize=64)
def _get_transformer(zone_number: int, south: bool) -> Transformer:
    """Return a cached transformer from WGS84 to UTM coordinates."""
    epsg = 32700 + zone_number if south else 32600 + zone_number
    return Transformer.from_crs(
        "EPSG:4326", CRS.from_epsg(epsg), always_xy=True
    )


def wgs84_to_utm(lat: float, lon: float, zone: str) -> tuple[float, float]:
    """Convert WGS84 coordinates (DD.DDDDDD) to UTM."""
    if len(zone) < 2:
        raise ValueError(f"Invalid UTM zone: {zone!r}")

    zone_number = int(zone[:-1])
    hemisphere = zone[-1].upper()

    if hemisphere not in ("N", "S"):
        raise ValueError(f"Zone must end with N or S, got: {zone!r}")

    south = hemisphere == "S"

    transformer = _get_transformer(zone_number, south)

    return transformer.transform(lon, lat)


def nmea_to_decimal(value: SupportsFloat, hemisphere: str) -> float:
    """Convert NMEA coordinate (DDMM.MMMMMM) to decimal degrees (DD.DDDDDD)."""
    value = float(value)

    degrees = int(value // 100)
    minutes = value - degrees * 100

    decimal = degrees + minutes / 60

    if hemisphere.upper() in ("S", "W"):
        decimal = -decimal
    elif hemisphere.upper() not in ("N", "E"):
        raise ValueError(f"Invalid hemisphere: {hemisphere!r}")

    return decimal


def deg_to_dms(value: float) -> str:
    """Converts decimal degrees to a degrees-minutes-seconds (DMS) string."""
    d = int(abs(value))
    m = int((abs(value) - d) * 60)
    s = (abs(value) - d - m / 60) * 3600
    return f"{d}°{m:02d}'{s:06.3f}\""
