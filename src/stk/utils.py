import struct
import time
import tkinter as tk
from functools import wraps
from pathlib import Path
from tkinter import filedialog
from typing import Any


def get_file() -> str:
    """Select file. Returns folder path."""

    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select file", filetypes=[("All files", "*.*")]
    )
    root.destroy()
    print("Selected file: ", file_path, end="\n\n")
    return file_path


def get_folder() -> str:
    """Select folder. Returns file path"""

    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select folder")
    root.destroy()
    print("Selected folder: ", folder_path, end="\n\n")
    return folder_path


def create_folder(folder_name: str, path: Path) -> Path:
    """Create folder in selected dirrectory."""

    folder_path = Path(path) / folder_name
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path


def get_paths(folder_path: Path, formats=(".sgy", ".segy")):
    folder = Path(folder_path)
    file_paths = []
    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in formats:
            file_paths.append(file)
    print(f"Number of files found: {len(file_paths)}", end="\n\n")
    return file_paths


def get_size_mb(file_path):
    size_mb = round(Path(file_path).stat().st_size / (1024 * 1024), 2)
    return size_mb


def pack(fmt: str, hdr: bytearray, offset: int, value: Any) -> None:
    """Pack value into header buffer at specified offset."""

    struct.pack_into(fmt, hdr, offset, value)


def unpack(byte_order: str, fmt: str, data: bytes, byte_range: tuple[int, int]) -> Any:
    """Extract and unpack a value from a byte sequence."""

    start, end = byte_range
    return struct.unpack(byte_order + fmt, data[start:end])[0]


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        wrapper.elapsed_time = end - start
        return result
    wrapper.elapsed_time = 0
    return wrapper
