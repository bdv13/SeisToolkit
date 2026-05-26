from math import hypot

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString


def export_csv(dataset, path):
    df = pd.DataFrame(
        {
            "Line": dataset.name,
            "FFID": dataset.ffids,
            "SOU_X": dataset.sou_x_list,
            "SOU_Y": dataset.sou_y_list,
            "CUMDIST": dataset.cumdists,
            "STEP": dataset.steps,
        }
    )
    df["SOU_X"] = df["SOU_X"].map(lambda x: f"{x:.2f}")
    df["SOU_Y"] = df["SOU_Y"].map(lambda x: f"{x:.2f}")
    df["CUMDIST"] = df["CUMDIST"].map(lambda x: f"{x:.2f}")
    df["STEP"] = df["STEP"].map(lambda x: f"{x:.2f}")
    df.to_csv(path, index=False, encoding="utf-8")


def compute_cumdist(dataset):
    shots = list(zip(dataset.sou_x_list, dataset.sou_y_list))
    steps = []
    cumdists = [0]
    for idx in range(1, len(shots)):
        x1, y1 = shots[idx - 1]
        x2, y2 = shots[idx]
        step = hypot(x2 - x1, y2 - y1)
        steps.append(step)
        cumdists.append(cumdists[-1] + step)
    steps.append(steps[-2])
    dataset.cumdists = cumdists
    dataset.steps = steps
    return cumdists, steps


class TrackExporter:
    def __init__(self, crs):
        self.crs = crs
        self.lines = []
        self.ids = []

    def add_dataset(self, dataset):
        points = list(zip(dataset.sou_x_list, dataset.sou_y_list))
        self.lines.append(LineString(points))
        self.ids.append(dataset.id)
        return True

    def to_gdf(self):
        return gpd.GeoDataFrame(
            {"id": self.ids}, geometry=self.lines, crs=self.crs
        )

    def export(self, path):
        gdf = self.to_gdf()
        gdf.to_file(path, layer="tracklines", driver="GPKG")
