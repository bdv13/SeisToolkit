from pathlib import Path
from typing import Literal

from .select import select_folder


def get_files(

    folder: Path = None,
    file_formats: tuple[str, ...] = (".sgy", ".segy"),
    output_type: Literal['names', 'paths'] = 'paths',
    export: bool = False,

) -> list[Path] | list[str] | None:

    """Collect file paths or names with specified extensions."""

    folder_path = Path(folder) if folder else select_folder(
        "Select folder with files"
    )

    files = [
        file
        for file in folder_path.iterdir()
        if file.is_file() and file.suffix.lower() in file_formats
    ]

    if not files:
        print("No files found!")
        return None

    if output_type == "paths":
        result = files
    else:
        result = [file.name for file in files]

    if export:
        output_name = (
            "file_paths.txt"
            if output_type == "paths"
            else "file_names.txt"
        )

        output_file = folder_path / output_name
        output_file.write_text(
            "\n".join(str(item) for item in result),
            encoding="utf-8",
        )

    return result
