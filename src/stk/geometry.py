import os
from math import hypot, floor
from typing import SupportsFloat
from functools import lru_cache

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
from pyproj import CRS, Transformer


@lru_cache(maxsize=64)
def _get_transformer_inverse(zone_number: int, south: bool) -> Transformer:
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
    epsg = 32700 + zone_number if south else 32600 + zone_number
    return Transformer.from_crs("EPSG:4326", CRS.from_epsg(epsg), always_xy=True)


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
    """Convert NMEA coordinate (DDMM.MMMMMM) to decimal degrees (DD.DDDDDD). """
    value = float(value)

    degrees = int(value // 100)
    minutes = value - degrees * 100

    decimal = degrees + minutes / 60

    if hemisphere.upper() in ("S", "W"):
        decimal = -decimal
    elif hemisphere.upper() not in ("N", "E"):
        raise ValueError(f"Invalid hemisphere: {hemisphere!r}")

    return decimal


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


def get_geometry(dataset) -> list[tuple[float, float]]:

    coordinates = []

    raw_sac = dataset.traces[0].sac

    sac = raw_sac if raw_sac > 0 else 1 / abs(raw_sac) if raw_sac < 0 else 1
    for trace in dataset.traces:
        coordinates.append((trace.sou_x * sac, trace.sou_y * sac))

    return coordinates


def compute_cumdist(coordinates):

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
    def __init__(self, crs):
        self.crs = crs
        self.lines = []
        self.names = []

    def add_dataset(self, dataset):
        points = get_geometry(dataset)
        self.lines.append(LineString(points))
        self.names.append(dataset.name)

    def to_gdf(self):
        return gpd.GeoDataFrame({"Line": self.names}, geometry=self.lines, crs=self.crs)

    def export_gpkg(self, output_folder):
        gdf = self.to_gdf()
        file_path = os.path.join(output_folder, "tracklines.gpkg")
        gdf.to_file(file_path, layer="tracklines", driver="GPKG")

    @staticmethod
    def export_csv(dataset, output_folder):

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
