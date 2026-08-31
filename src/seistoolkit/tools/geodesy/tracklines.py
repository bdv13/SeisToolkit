import os
from math import hypot

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString


def get_geometry(
    dataset,
    fields: tuple[str, str] = ("sou_x", "sou_y"),
) -> list[tuple[float, float]]:
    """Return geometry coordinates."""
    x_field, y_field = fields
    return [
        (getattr(trace, x_field), getattr(trace, y_field))
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

    def __init__(self, crs, coord_fields=("sou_x", "sou_y")):
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
            {"Line": self.names}, geometry=self.lines, crs=self.crs
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
