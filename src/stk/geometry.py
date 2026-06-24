import os
from math import hypot

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

import stk.utils as u
from stk.config import proj_set
from stk.io_data import sgy_input


def get_geometry(dataset) -> tuple[float, float]:

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


@u.timer
def export_nav(folder_path=None, crs=proj_set["proj_crs"], csv=False):

    if folder_path is None:
        folder_path = u.get_folder()

    TracksExport = TracksExporter(crs)

    file_paths = u.get_paths(folder_path)
    output_path = u.create_folder('output', folder_path)

    for idx, file_path in enumerate(file_paths):
        current_dataset = sgy_input(file_path)
        TracksExport.add_dataset(current_dataset)
        if csv:
            TracksExport.export_csv(current_dataset, output_path)

    TracksExport.export_gpkg(output_path)


if __name__ == "__main__":
    print("Please select folder with seg files", end="\n\n")
    export_nav()
    print(f"Done! Complited in {export_nav.elapsed_time:.3f} sec", end="\n\n")
