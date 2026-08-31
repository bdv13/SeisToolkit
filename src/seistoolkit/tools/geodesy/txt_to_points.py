from pathlib import Path

import geopandas as gpd
import pandas as pd


def txt_to_points(
    file_path: Path,
    coord_cols: tuple[str, str],
    crs: str,
    sep: str = " ",
) -> None:
    """Convert a TXT file with X/Y coordinates into a GeoPackage."""
    data = pd.read_csv(file_path, sep=sep, header=0)

    x_col, y_col = coord_cols

    # Ensure coordinates are numeric and fail clearly on invalid values.
    data[x_col] = pd.to_numeric(data[x_col], errors="raise")
    data[y_col] = pd.to_numeric(data[y_col], errors="raise")

    geometry = gpd.points_from_xy(data[x_col], data[y_col])

    gdf = gpd.GeoDataFrame(data, geometry=geometry, crs=crs)

    output_path = file_path.with_suffix(".gpkg")
    gdf.to_file(
        output_path,
        layer=file_path.stem,
        driver="GPKG",
    )
