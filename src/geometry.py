from math import hypot

import os
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString


def get_geometry(dataset):
    """Get geometry from the dataset"""

    coordinates = []

    if dataset.tr_hdrs['UNITS'][0] != 1:
        print(f"{dataset.name} geometry not in projected coordinates!")
        return None

    raw_sac = dataset.tr_hdrs['SAC'][0]
    sac = raw_sac if raw_sac > 0 else 1 / abs(raw_sac) if raw_sac < 0 else 1

    for x, y in zip(dataset.tr_hdrs['SOU_X'], dataset.tr_hdrs['SOU_Y']):
        coordinates.append((x * sac, y * sac))

    return coordinates


def compute_cumdist(dataset):

    coordinates = get_geometry(dataset)
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
        return True

    def to_gdf(self):
        return gpd.GeoDataFrame(
            {"Line": self.names}, geometry=self.lines, crs=self.crs
        )

    def export(self, path):
        gdf = self.to_gdf()
        file_path = os.path.join(path, "tracklines.gpkg")
        gdf.to_file(file_path, layer="tracklines", driver="GPKG")


def export_csv(dataset, output_folder):

    coordinates = get_geometry(dataset)
    cumdists, steps = compute_cumdist(dataset)

    df = pd.DataFrame(
        {
            "Line": dataset.name,
            "FFID": dataset.tr_hdrs['FFID'],
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
