import seistoolkit.utils as u
from seistoolkit.config import UTM_EPSG
from seistoolkit.geometry import txt_to_points

CRS = '36N'


def main():
    """Batch convert TXT files to points."""

    folder_path = u.select_folder("Select folder with txt files")
    txt_files = u.get_paths(folder_path, (".txt",))

    for txt_file in txt_files:
        txt_to_points(
            txt_file,
            coord_cols=("SOU_X", "SOU_Y"),
            separator='\t',
            crs=UTM_EPSG[CRS],
        )


if __name__ == "__main__":
    main()
    print('Done!')
