from seistoolkit.models import Picks
from seistoolkit.utils import create_folder, get_paths, select_folder


def main():
    """Batch txt files convert to RadExPro picks."""

    folder_path = select_folder("Please select folder with txt files.")
    output_folder = create_folder("picks", folder_path)
    file_paths = get_paths(folder_path, (".txt",))

    for file_path in file_paths:
        pick = Picks.import_txt(
            file_path,
            ("S_LINE", "FFID", "CHAN"),
            "FBPICK",
        )

        pick.export_rdx_pick(
            "FFID",
            "CHAN",
            output_folder / f"{file_path.stem}.txt"
        )


if __name__ == "__main__":
    main()
    print("Done!")
