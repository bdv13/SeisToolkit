import os
import time
import tkinter as tk
from functools import wraps
from pathlib import Path
from tkinter import filedialog

import pandas as pd

from config import log_dict


def get_folder():
    """Select folder with sgy files"""

    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select folder")
    root.destroy()
    print("Selected folder: ", folder_path, end="\n\n")
    return folder_path


def get_sgy_paths(folder_path):
    formats = (".sgy", ".segy")
    folder = Path(folder_path)
    number_files = 0
    file_paths = []
    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in formats:
            file_paths.append(file)
            number_files += 1
    print(f'Number of files found: {number_files}', end="\n\n")
    return file_paths


def create_output_dir():
    project_root = Path(__file__).resolve().parent
    proj_dir_path = project_root / 'output'
    proj_dir_path.mkdir(exist_ok=True)
    return proj_dir_path


def create_log_path(path):
    log_path = os.path.join(path, "Log.xlsx")
    df = pd.DataFrame(columns=list(log_dict.keys()))
    df.to_excel(log_path, index=False, engine="openpyxl")
    return log_path


def get_size_mb(file_path):
    size_mb = round(Path(file_path).stat().st_size / (1024 * 1024), 2)
    return size_mb


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
