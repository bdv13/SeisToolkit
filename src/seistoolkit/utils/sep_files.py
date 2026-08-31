import shutil
from pathlib import Path
from typing import Literal

from .manage_folder import create_folder
from .select import select_file, select_folder


def sep_files(
    operation: Literal["copy", "move"] = "copy",
    input_type: Literal["paths", "names"] = "paths",
) -> None:
    """Copy or move files listed in a TXT file to a separate folder."""

    folder_path = select_folder("Select folder with files")
    files_list = select_file("Select TXT file")

    output_folder = create_folder("separated_files", folder_path)

    with open(files_list, "r", encoding="utf-8") as f:
        files = [line.strip() for line in f if line.strip()]

    counter = 0
    total = len(files)

    for file in files:
        if input_type == "paths":
            source_file = Path(file)
            file_name = source_file.name

        elif input_type == "names":
            file_path = Path(file)
            file_name = file_path.name

            if file_path.suffix:
                source_file = folder_path / file_name
            else:
                matches = list(folder_path.glob(f"{file_name}.*"))

                if not matches:
                    raise FileNotFoundError(f"File not found: {file_name}")

                source_file = matches[0]
                file_name = source_file.name

        else:
            raise ValueError(f"Unknown input type: {input_type}")

        source_file = source_file.resolve()
        destination_file = (Path(output_folder) / file_name).resolve()

        if source_file == destination_file:
            raise ValueError(
                f"Source and destination are the same file:\n{source_file}"
            )

        if not source_file.is_file():
            raise FileNotFoundError(f"Source file not found: {source_file}")

        if operation == "copy":
            shutil.copy2(source_file, destination_file)

        elif operation == "move":
            shutil.move(source_file, destination_file)

        else:
            raise ValueError(f"Unknown operation: {operation}")

        counter += 1

    print(f"Successfully {operation}ed {counter} of {total} files.")
