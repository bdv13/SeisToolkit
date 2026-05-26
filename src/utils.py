import os
import time
import tkinter as tk
from functools import wraps
from pathlib import Path
from tkinter import filedialog

import pandas as pd

from config import log_dict, proj_settings


def get_folder():
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select folder with sgy files")
    root.destroy()
    print("Selected folder: ", folder_path, end="\n\n")
    return folder_path


def get_file_path(folder_path):
    formats = (".sgy", ".segy")
    folder = Path(folder_path)
    number_files = 0
    file_paths = []
    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in formats:
            file_paths.append(file)
            number_files += 1
    print("Number of files: ", number_files)
    return number_files, file_paths


def create_proj_dir():
    project_root = Path(__file__).resolve().parent
    proj_dir_path = project_root / proj_settings["proj_dir"]
    proj_dir_path.mkdir(exist_ok=True)
    return proj_dir_path


def create_log_file(path):
    log_path = os.path.join(path, "Log.xlsx")
    df = pd.DataFrame(columns=list(log_dict.keys()))
    df.to_excel(log_path, index=False, engine="openpyxl")
    print("\nLog file created and placed here: ", path, end="\n\n")
    return log_path


def write_log_file(SGYFile, log_path):
    log_df = pd.read_excel(log_path)
    row = {}
    for column_name, attr_name in log_dict.items():
        row[column_name] = getattr(SGYFile, attr_name)
    log_df.loc[len(log_df)] = row
    log_df.to_excel(log_path, index=False, engine="openpyxl")


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
