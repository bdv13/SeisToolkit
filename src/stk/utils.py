import shutil
import struct
import time
import tkinter as tk
from functools import wraps
from pathlib import Path
from tkinter import filedialog
from typing import Any, Literal


def select_file() -> Path | None:
    """Select file. Returns file path."""
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select file", filetypes=[("All files", "*.*")]
    )
    root.destroy()

    if not file_path:
        print("File is not selected!", end="\n")
        return

    return Path(file_path)


def select_folder() -> Path | None:
    """Select folder. Returns folder path."""
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select folder")
    root.destroy()

    if not folder_path:
        return

    return Path(folder_path)


def create_folder(folder_name: str, path: Path) -> Path:
    """Create folder in selected directory and return it path."""
    folder_path = path / folder_name
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path


def get_paths(
        folder_path: Path,
        formats: tuple[str, ...] = (".sgy", ".segy"),
        export: bool = False
) -> list[Path] | None:
    """Collect file paths with specified extensions."""
    folder = Path(folder_path)
    file_paths = []
    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in formats:
            file_paths.append(file)

    if not file_paths:
        print("No files found!", end="\n\n")
        return

    if export:
        output_file = folder / "file_paths.txt"

        output_file.write_text(
            "\n".join(str(path) for path in file_paths), encoding="utf-8"
        )

    return file_paths


def get_size_mb(file_path: Path) -> float:
    """Get file size in mb."""
    return file_path.stat().st_size / 1024**2


def pack(fmt: str, hdr: bytearray, offset: int, value: Any) -> None:
    """Pack value into header buffer at specified offset."""
    struct.pack_into(fmt, hdr, offset, value)


def unpack(
        byte_order: str,
        fmt: str, data: bytes,
        byte_range: tuple[int, int]
) -> Any:
    """Extract and unpack a value from a byte sequence."""
    start, end = byte_range
    return struct.unpack(byte_order + fmt, data[start:end])[0]


def separate_files(operation: Literal["copy", "move"] = "copy"):
    """Copy or move files listed in a text file to a separate folder."""
    folder_path = select_folder()
    files_list = select_file()

    output_folder = create_folder("separated_files", folder_path)

    with open(files_list, "r", encoding="utf-8") as f:
        files = [line.strip() for line in f if line.strip()]

    for file in files:
        file_name = Path(file).name

        source_file = folder_path / file_name
        destination_file = Path(output_folder) / file_name

        if not source_file.exists():
            print(f"File not found: {source_file}")
            continue

        if operation == "copy":
            shutil.copy2(source_file, destination_file)

        elif operation == "move":
            shutil.move(source_file, destination_file)

        else:
            raise ValueError("Unknown command!")


def delete(path: Path) -> None:
    """Delete a file or directory (recursively)."""
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    if path.is_file() or path.is_symlink():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    else:
        raise ValueError(f"Unsupported path type: {path}")


def timer(func):
    """Estimate function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        wrapper.elapsed_time = end - start
        return result
    wrapper.elapsed_time = 0
    return wrapper
