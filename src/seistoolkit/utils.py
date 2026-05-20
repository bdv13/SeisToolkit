import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

import pandas as pd

from seistoolkit.config import log_hdrs


def get_folder():
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select folder with sgy files")
    root.destroy()
    print("Selected folder: ", folder_path)
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


def create_log_file():
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    log_path = os.path.join(desktop_path, "Log.xlsx")
    df = pd.DataFrame(columns=list(log_hdrs.keys()))
    df.to_excel(log_path, index=False, engine="openpyxl")
    print("\nLog file created and placed here: ", log_path)
    return log_path


def write_log_file(SGYFile, log_path):
    log_df = pd.read_excel(log_path)
    row = {}
    for column_name, attr_name in log_hdrs.items():
        row[column_name] = getattr(SGYFile, attr_name)
    log_df.loc[len(log_df)] = row
    log_df.to_excel(log_path, index=False, engine="openpyxl")
