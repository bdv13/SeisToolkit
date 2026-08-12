import seistoolkit.utils as u
from seistoolkit.config import UTM_EPSG
from seistoolkit.geometry import TracksExporter
from seistoolkit.segy import sgy_input

UTM_ZONE = '35N'
COORD_HDRS = ('sou_x', 'sou_y')


@u.timer
def export_nav(
    folder_path=None,
    crs=f"EPSG:{UTM_EPSG[UTM_ZONE]}",
    source_hdrs=COORD_HDRS,
    csv=False
):
    """Export navigation data from SEG-Y files to GIS formats."""
    if folder_path is None:
        folder_path = u.select_folder()

    TracksExport = TracksExporter(crs, source_hdrs)

    file_paths = u.get_paths(folder_path)
    output_path = u.create_folder("output", folder_path)

    for idx, file_path in enumerate(file_paths):
        current_dataset = sgy_input(file_path)
        TracksExport.add_dataset(current_dataset)
        if csv:
            TracksExport.export_csv(current_dataset, output_path)

    TracksExport.export_gpkg(output_path)


if __name__ == "__main__":
    print()
    print("Please select folder with seg files", end="\n\n")
    export_nav()
    print(f"Done! Complited in {export_nav.elapsed_time:.3f} sec", end="\n\n")
