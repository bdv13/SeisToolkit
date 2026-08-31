from seistoolkit.config import UTM_EPSG
from seistoolkit.tools.geodesy import txt_to_points
from seistoolkit.utils import get_files, select_folder

CRS = "36N"


def main():
    """Batch convert TXT files to points."""

    folder_path = select_folder("Select folder with txt files")
    txt_files = get_files(folder_path, (".txt",))

    for txt_file in txt_files:
        txt_to_points(
            txt_file,
            coord_cols=("SOU_X", "SOU_Y"),
            sep="\t",
            crs=UTM_EPSG[CRS],
        )


if __name__ == "__main__":
    main()
    print("Done!")
