import os
from dataclasses import dataclass
from functools import lru_cache
from math import floor, hypot
from typing import SupportsFloat

import geopandas as gpd
import numpy as np
import pandas as pd
from pyproj import CRS, Transformer
from scipy.interpolate import interp1d
from shapely.geometry import LineString


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
        "EPSG:4326",
        CRS.from_epsg(epsg),
        always_xy=True
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
    """ Converts decimal degrees to a degrees-minutes-seconds (DMS) string."""
    d = int(abs(value))
    m = int((abs(value) - d) * 60)
    s = (abs(value) - d - m / 60) * 3600
    return f'{d}°{m:02d}\'{s:06.3f}"'


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


def get_geometry(
        dataset,
        fields: tuple[str, str] = ("sou_x", "sou_y"),
    ) -> list[tuple[float, float]]:
    """Return geometry coordinates."""
    x_field, y_field = fields
    return [
        (
            getattr(trace, x_field),
            getattr(trace, y_field)
        )
        for trace in dataset.traces
    ]


def compute_cumdist(coordinates):
    """Compute stepwise and cumulative distances between coordinates."""
    steps = []
    cumdists = [0]

    for idx in range(1, len(coordinates)):
        x1, y1 = coordinates[idx - 1]
        x2, y2 = coordinates[idx]

        step = hypot(x2 - x1, y2 - y1)
        steps.append(step)

        cumdists.append(cumdists[-1] + step)

    steps.append(steps[-2])

    return cumdists, steps


class TracksExporter:
    """Utility class for exporting and processing seismic trace geometry."""

    def __init__(self, crs, coord_fields=('sou_x', 'sou_y')):
        self.crs = crs
        self.coord_fields = coord_fields
        self.lines = []
        self.names = []

    def add_dataset(self, dataset):
        """Add a dataset geometry to the exporter."""
        points = get_geometry(dataset, self.coord_fields)
        self.lines.append(LineString(points))
        self.names.append(dataset.name)

    def to_gdf(self):
        """Convert stored line geometries to a GeoDataFrame."""
        return gpd.GeoDataFrame(
            {"Line": self.names},
            geometry=self.lines,
            crs=self.crs
        )

    def export_gpkg(self, output_folder):
        """Export stored track geometries to a GeoPackage file."""
        gdf = self.to_gdf()
        file_path = os.path.join(output_folder, "tracklines.gpkg")
        gdf.to_file(file_path, layer="tracklines", driver="GPKG")

    @staticmethod
    def export_csv(dataset, output_folder):
        """Export dataset geometry and trace metadata to a CSV file."""
        coordinates = get_geometry(dataset)
        cumdists, steps = compute_cumdist(coordinates)

        df = pd.DataFrame(
            {
                "Line": dataset.name,
                "FFID": [trace.ffid for trace in dataset.traces],
                "SOU_X": [coordinate[0] for coordinate in coordinates],
                "SOU_Y": [coordinate[1] for coordinate in coordinates],
                "CUMDIST": cumdists,
                "STEP": steps,
            }
        )

        df["SOU_X"] = df["SOU_X"].map(lambda x: f"{x:.2f}")
        df["SOU_Y"] = df["SOU_Y"].map(lambda x: f"{x:.2f}")
        df["CUMDIST"] = df["CUMDIST"].map(lambda x: f"{x:.2f}")
        df["STEP"] = df["STEP"].map(lambda x: f"{x:.2f}")

        file_path = os.path.join(output_folder, dataset.name + ".csv")
        df.to_csv(file_path, index=False, encoding="utf-8")


def remove_duplicates(data: list[tuple[float, float]]) -> None:
    """Mark consecutive duplicate navigation points as (None, None)."""
    prev = data[0]
    for i in range(1, len(data)):
        if data[i] == prev:
            data[i] = (None, None)
        else:
            prev = data[i]


def linear_interp(data: list[tuple[float, float]], rouding=2) -> None:
    """Linearly interpolate 2D navigation track in-place."""

    def interp(v):
        return interp1d(
            t[mask],
            v[mask],
            kind="linear",
            bounds_error=False,
            fill_value="extrapolate"
        )(t)

    t = np.arange(len(data))

    arr = np.array(
        [(np.nan, np.nan) if p is None else p for p in data], dtype=float
    )

    mask = ~np.isnan(arr).any(axis=1)
    if mask.sum() < 2:
        raise ValueError("Not enough points for interpolation")

    arr[:, 0] = interp(arr[:, 0])
    arr[:, 1] = interp(arr[:, 1])

    for i in range(len(data)):
        data[i] = (
            round(float(arr[i, 0]), rouding), round(float(arr[i, 1]), rouding))


def track_segments(
        data: list[tuple[float, float]],
        threshold: float = 10
) -> list[list[tuple[float, float]]]:
    """Split track into continuous segments based on point spacing."""
    if not data:
        raise ValueError("Data must contain at least one coordinate")

    _, steps = compute_cumdist(data)

    segments = []
    start = 0

    for i, step in enumerate(steps):
        if step > threshold:
            segments.append(data[start:i + 1])
            start = i + 1

    segments.append(data[start:])

    return segments


@dataclass
class NMEALogStats:
    """Dataclass to collect NMEA log statistics."""

    # Line statistics
    total: int = 0

    # Message counters
    gga_count: int = 0
    zda_count: int = 0
    rmc_count: int = 0
    hdt_count: int = 0
    others_count: int = 0

    # Skipped lines
    invalid: int = 0
    missing_data: int = 0

    # Errors
    zda_errors: int = 0
    hdt_errors: int = 0
    rmc_errors: int = 0
    gga_errors: int = 0

    @property
    def parse_errors(self) -> int:
        return (
            self.zda_errors
            + self.hdt_errors
            + self.rmc_errors
            + self.gga_errors
        )

    @property
    def skipped(self) -> int:
        return (self.invalid + self.parse_errors + self.missing_data)

    @property
    def skipped_percent(self) -> float:
        if self.total == 0:
            return 0.0
        return self.skipped / self.total * 100

    def print_stats(self):
        print(f"Total: {self.total}")
        print(f"GGA: {self.gga_count}")
        print(f"ZDA: {self.zda_count}")
        print(f"RMC: {self.rmc_count}")
        print(f"HDT: {self.hdt_count}")
        print(f"Other: {self.others_count}")
        print()
        print(f"Skipped: {self.skipped} ({self.skipped_percent:.2f}%)")
        print(f"Invalid: {self.invalid}")
        print(f"Missing: {self.missing_data}")
        print(
            f"Parse issues: {self.parse_errors} "
            f"(GGA: {self.gga_errors}, "
            f"ZDA: {self.zda_errors}, "
            f"RMC: {self.rmc_errors}, "
            f"HDT: {self.hdt_errors})"
        )
        print()
