import shutil
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

SEISMIC_EXTS = {".sgy", ".segy", ".sgd", ".segd"}
DEFAULT_INT = 2000

GUI_PADX = 2
GUI_PADY = 4


def _validate_inputs(
    input_path: Path | None,
    output_path: Path | None,
    interval_ms: int,
) -> tuple[list[Path], int, int]:
    """Validate paths and interval, then prepare the output folder."""

    if not input_path:
        raise FileNotFoundError("Please select input folder.")

    if not input_path.is_dir():
        raise FileNotFoundError("Input folder does not exist.")

    if not output_path:
        raise FileNotFoundError("Please select output folder.")

    if not output_path.is_dir():
        raise FileNotFoundError("Output folder does not exist.")

    try:
        interval_ms = int(interval_ms)
    except TypeError, ValueError:
        raise ValueError("Shot interval must be a number.")

    if not 0 < interval_ms <= 9999:
        raise ValueError("Shot interval must be between 1 and 9999 ms.")

    files_paths = [
        path
        for path in input_path.iterdir()
        if path.is_file() and path.suffix.lower() in SEISMIC_EXTS
    ]

    if not files_paths:
        raise FileNotFoundError("No seismic files found in input folder.")

    files_amount = len(files_paths)

    print(f"\nInput folder path: {input_path}")
    print(f"Output folder path: {output_path}")
    print(f"Shot interval (ms) {interval_ms}")
    print(f"Amount of files in input folder: {files_amount}")

    return files_paths, files_amount, interval_ms


def simulate_seismic_files(
    input_path: str | Path | None,
    output_path: str | Path | None,
    interval_ms: int = DEFAULT_INT,
    stop_event: threading.Event | None = None,
) -> None:
    """Simulate seismic acquisition by copying files at a fixed interval."""

    input_path = Path(input_path) if input_path else None
    output_path = Path(output_path) if output_path else None

    file_paths, file_amount, interval_ms = _validate_inputs(
        input_path,
        output_path,
        interval_ms,
    )

    print("\nStarted... Press Ctrl + C to stop simulation.", end="\n")

    try:
        for file_number, file_path in enumerate(file_paths, start=1):
            if stop_event and stop_event.wait(interval_ms / 1000):
                print("\nSimulation stopped by user.")
                return

            print(
                f"Shot {file_number} of {file_amount} "
                f"({file_path.stem}). "
                f"[{datetime.now():%Y-%m-%d %H:%M:%S}]"
            )

            shutil.copy2(file_path, output_path / file_path.name)

    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")

    else:
        print("\nSimulation completed. All files used.")


def resource_path(relative_path: str) -> Path:
    """Get path to bundled resource."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / relative_path

    return Path(__file__).resolve().parent.parent / relative_path


class SimSeisGUI(tk.Tk):
    """Application GUI."""

    def __init__(self):
        super().__init__()

        self.title("SimSeis")
        self.geometry("500x225")
        self.resizable(False, False)

        self.iconbitmap(resource_path("assets/simseis.ico"))

        self.stop_event = threading.Event()

        self._create_widgets()
        self._center_window()

    def _center_window(self) -> None:
        self.update_idletasks()

        width = self.winfo_width()
        height = self.winfo_height()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.geometry(f"{width}x{height}+{x}+{y}")

    def _select_input_folder(self) -> None:
        path = filedialog.askdirectory(title="Select input folder")

        if path:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, path)

    def _select_output_folder(self) -> None:
        path = filedialog.askdirectory(title="Select output folder")

        if path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, path)

    def _get_input_path(self) -> Path | None:
        value = self.input_entry.get().strip()
        return Path(value) if value else None

    def _get_output_path(self) -> Path | None:
        value = self.output_entry.get().strip()
        return Path(value) if value else None

    def _set_status(self, text: str) -> None:
        self.status_label.config(text=f"Status: {text}")

    def _simulation_worker(self) -> None:
        try:
            simulate_seismic_files(
                self._get_input_path(),
                self._get_output_path(),
                self.interval_entry.get(),
                self.stop_event,
            )
        except (FileNotFoundError, ValueError, OSError) as error:
            self.simulation_error = str(error)
        except Exception as error:
            self.simulation_error = f"{type(error).__name__}: {error}"

    def _start_simulation(self):
        self.stop_event.clear()

        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

        self.simulation_error = None
        self._set_status("Running")

        self.simulation_thread = threading.Thread(
            target=self._simulation_worker,
            daemon=True,
        )

        self.simulation_thread.start()
        self.after(100, self._check_simulation)

    def _stop_simulation(self):
        self.stop_event.set()
        self.stop_button.config(state="disabled")

    def _check_simulation(self):
        if self.simulation_thread.is_alive():
            self.after(100, self._check_simulation)
            return

        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

        if self.simulation_error:
            self._set_status("Error")
            messagebox.showerror("Simulation error", self.simulation_error)

        elif self.stop_event.is_set():
            self._set_status("Stopped by user.")

        else:
            self._set_status("Simulation completed. All files used.")

    def _create_widgets(self):
        self.columnconfigure(0, weight=1)

        # ============== Input / Output paths ==============

        self.input_label = ttk.Label(
            self, text="Select folder with shots (*.sgy or *.sgd files):"
        )
        self.input_label.grid(
            row=0, column=0, padx=GUI_PADX, pady=GUI_PADY, ipadx=80, sticky="w"
        )

        self.input_entry = ttk.Entry(self)
        self.input_entry.grid(
            row=1,
            column=0,
            padx=(GUI_PADX, 5),
            pady=GUI_PADY,
            ipadx=80,
            sticky="ew",
        )

        self.input_button = ttk.Button(
            self,
            text="Browse...",
            command=self._select_input_folder,
        )
        self.input_button.grid(
            row=1, column=1, padx=(0, GUI_PADX), pady=GUI_PADY, sticky="w"
        )

        self.output_label = ttk.Label(
            self, text="Select folder for acquisition simulation:"
        )
        self.output_label.grid(
            row=2, column=0, padx=GUI_PADX, pady=GUI_PADY, ipadx=80, sticky="w"
        )

        self.output_entry = ttk.Entry(self)
        self.output_entry.grid(
            row=3,
            column=0,
            padx=(GUI_PADX, 5),
            pady=GUI_PADY,
            ipadx=80,
            sticky="ew",
        )

        self.output_button = ttk.Button(
            self,
            text="Browse...",
            command=self._select_output_folder,
        )
        self.output_button.grid(
            row=3, column=1, padx=(0, GUI_PADX), pady=GUI_PADY, sticky="w"
        )

        # ============== Shot interval ==============

        self.interval_label = ttk.Label(self, text="Enter shot interval (ms):")
        self.interval_label.grid(
            row=4, column=0, padx=GUI_PADX, pady=GUI_PADY, ipadx=80, sticky="w"
        )

        self.interval_entry = ttk.Entry(self, width=8)
        self.interval_entry.insert(0, DEFAULT_INT)
        self.interval_entry.grid(
            row=4,
            column=0,
            padx=(GUI_PADX, 5),
            pady=GUI_PADY,
            ipadx=10,
            sticky="e",
        )

        # ============== Start / Stop buttons ==============

        self.start_button = ttk.Button(
            self, text="Start", width=11, command=self._start_simulation
        )

        self.start_button.grid(
            row=5, column=0, padx=(GUI_PADX, 85), pady=GUI_PADY, sticky="e"
        )

        self.stop_button = ttk.Button(
            self,
            text="Stop",
            width=11,
            state="disabled",
            command=self._stop_simulation,
        )

        self.stop_button.grid(
            row=5, column=0, padx=GUI_PADX, pady=GUI_PADY, sticky="e"
        )

        # ============== Status ==============

        self.status_label = ttk.Label(self, text="Status: ")
        self.status_label.grid(
            row=6, column=0, padx=GUI_PADX, pady=GUI_PADY, ipadx=80, sticky="w"
        )
        self._set_status("Ready")


if __name__ == "__main__":
    app = SimSeisGUI()
    app.mainloop()


# pyinstaller --onefile --windowed --icon=assets/simseis.ico --add-data
# "assets/simseis.ico;assets" scripts/simseis.py
