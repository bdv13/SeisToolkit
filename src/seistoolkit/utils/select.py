import tkinter as tk
from pathlib import Path
from tkinter import filedialog


def select_file(title='Select file') -> Path | None:
    """Select file. Returns file path."""
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title=title, filetypes=[("All files", "*.*")]
    )
    root.destroy()

    if not file_path:
        print("File is not selected!", end="\n")
        return

    print(f'Selected file: {file_path}', end="\n")

    return Path(file_path)


def select_folder(title='Select folder') -> Path | None:
    """Select folder. Returns folder path."""
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    folder_path = filedialog.askdirectory(title=title)
    root.destroy()

    if not folder_path:
        print("Folder is not selected!", end="\n")
        return

    print(f'Selected folder: {folder_path}', end="\n")

    return Path(folder_path)
