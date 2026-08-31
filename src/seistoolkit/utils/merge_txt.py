from pathlib import Path

from .get_files import get_files
from .select import select_folder


def merge_txt(

    folder: Path = None,
    output_name: str = "merged",
    has_header: bool = True,
    add_source_file: bool = True,
    source_file_sep: str = " ",

) -> Path:
    """Merge txt files from a folder into one file."""

    folder = Path(folder) if folder else select_folder(
        "Select folder with txt files"
    )

    file_paths = get_files(folder, (".txt",))

    if not file_paths:
        raise FileNotFoundError(f"No txt files found in {folder}")

    file_paths = sorted(file_paths)
    output_path = folder / f"{output_name}.txt"

    is_first_file = True

    with open(output_path, "w", encoding="utf-8") as output_file:
        for file_path in file_paths:
            with open(file_path, "r", encoding="utf-8") as input_file:
                for index, line in enumerate(input_file):
                    line = line.rstrip("\n")

                    if index == 0 and has_header:
                        if not is_first_file:
                            continue

                        if add_source_file:
                            line += f"{source_file_sep}FILE_NAME"

                    elif add_source_file:
                        source_name = file_path.name.replace(" ", "_")
                        line += f"{source_file_sep}{source_name}"

                    output_file.write(line + "\n")

            is_first_file = False

    return output_path
