import os
from datetime import datetime
from math import atan2, degrees
from pathlib import Path

import pandas as pd

from seistoolkit.config import FMT_DICT, LOG_DICT
from seistoolkit.tools.geodesy import compute_cumdist, get_geometry
from seistoolkit.tools.io import sgy_input
from seistoolkit.utils import create_folder, get_files, select_folder, timer


def get_size_mb(file_path: Path) -> float:
    """Get file size in mb."""
    return round(file_path.stat().st_size / 1024**2, 2)


def get_azimuth(dataset):
    """Return survey azimuth in degrees (0-360)."""
    dx = dataset.traces[-1].sou_x - dataset.traces[0].sou_x
    dy = dataset.traces[-1].sou_y - dataset.traces[0].sou_y
    if dx == 0 and dy == 0:
        raise ValueError("Start and end coordinates are identical.")
    try:
        return round((degrees(atan2(dx, dy)) + 360) % 360)
    except Exception:
        return None


def get_avg_speed(length, duration):
    """Return average survey speed in km/h."""
    try:
        hours, minutes = map(int, duration.split(":"))
        time_hours = hours + minutes / 60
        avg_speed = length / time_hours
    except ZeroDivisionError, ValueError:
        return "No info"
    return round(avg_speed, 2)


def get_duration(dataset):
    """Return start time, end time and line duration (HH:MM)."""
    start = dataset.traces[0].get_dt()
    end = dataset.traces[-1].get_dt()

    if start == datetime.min and end == datetime.min:
        return None, None, None

    td = end - start
    total_minutes = int(td.total_seconds() // 60)
    hours, minutes = divmod(total_minutes, 60)
    duration = f"{hours:02}:{minutes:02}"

    return (
        start.strftime("%Y-%m-%d %H:%M:%S"),
        end.strftime("%Y-%m-%d %H:%M:%S"),
        duration,
    )


def delay_flag(dataset):
    """Check whether any trace contains a delay (relative recording delay)."""
    delays = []
    for trace in dataset.traces:
        delays.append(trace.relrect)
    if sum(delays) == 0:
        return False
    else:
        return True


def compute_line_stats(dataset):
    """Calculate line length and mean trace spacing for a dataset."""
    coordinates = get_geometry(dataset)
    cumdists, steps = compute_cumdist(coordinates)
    try:
        line_len_km = round(max(cumdists) / 1000, 2)
        mean_step = round(sum(steps) / len(steps), 2)
    except Exception:
        return ("Unknown", "Unknown")
    else:
        return line_len_km, mean_step


def trace_enum(dataset, start_value=0):
    """Compute sequential trace numbering range for a dataset."""
    trace_sol = start_value + 1
    trace_eol = start_value + len(dataset.traces)
    return trace_sol, trace_eol


def create_log_file(path):
    """Create an empty Excel log file for dataset information."""
    log_path = os.path.join(path, "Log.xlsx")
    df = pd.DataFrame(columns=list(LOG_DICT.keys()))
    df.to_excel(log_path, index=False, engine="openpyxl")
    return log_path


def write_log_file(log_file, log_path):
    """Append a log record to an Excel log file."""
    log_df = pd.read_excel(log_path)
    row = pd.Series(log_file)
    log_df = pd.concat([log_df, pd.DataFrame([row])], ignore_index=True)
    log_df.to_excel(log_path, index=False, engine="openpyxl")


@timer
def info(folder_path=None):
    """
    Analyze SEG-Y files in a folder and write summary log information.

    This function scans a directory for SEG-Y files, loads each dataset,
    computes basic acquisition and geometry statistics, and writes the
    results into a log file.

    For each dataset, the following information is collected:
    - line name
    - file size (MB)
    - number of traces
    - FFID start/end range (continuous trace numbering)
    - sample interval (ms)
    - record length (ms)
    - sampling frequency (Hz)
    - byte order
    - sample format
    - line length (km)
    - mean trace spacing (m)
    - delay recording flag

    The function creates an output folder and log file automatically
    if not provided.
    """
    if folder_path is None:
        folder_path = select_folder()

    file_paths = get_files(folder_path, formats=(".sgy", ".segy"))
    output_path = create_folder("output", folder_path)
    log_path = create_log_file(output_path)
    log_file = LOG_DICT.copy()

    current_trace = 0

    for idx, file_path in enumerate(file_paths):
        dataset = sgy_input(file_path)

        log_file["Line"] = dataset.name
        log_file["Size_mb"] = get_size_mb(file_path)
        log_file["Traces"] = len(dataset.traces)

        trace_sol, trace_eol = trace_enum(dataset, current_trace)
        current_trace = trace_eol
        length, mean_step = compute_line_stats(dataset)
        stime, etime, duration = get_duration(dataset)
        azimuth = get_azimuth(dataset)

        log_file["FFID_SOL"] = trace_sol
        log_file["FFID_EOL"] = trace_eol
        log_file["dt_ms"] = dataset.dt_us / 1000
        log_file["Length_ms"] = dataset.dt_us * dataset.numsmp / 1000
        log_file["Sample_Freq_hz"] = 1_000_000 / dataset.dt_us
        log_file["Byte_order"] = dataset.byte_order
        log_file["Format"] = FMT_DICT[dataset.fmt_code][0]
        log_file["Length_km"] = length
        log_file["Mean_step_m"] = mean_step
        log_file["Delay"] = delay_flag(dataset)
        log_file["Start_Time"] = stime if stime is not None else "No info"
        log_file["End_Time"] = etime if etime is not None else "No info"
        log_file["Duration"] = duration if duration is not None else "No info"
        log_file["Speed_kmh"] = get_avg_speed(length, duration)
        log_file["Azimuth"] = azimuth if azimuth is not None else "No info"

        write_log_file(log_file, log_path)


if __name__ == "__main__":
    print()
    print("Select folder with sgy files.", end="\n\n")
    info()
    print(f"Done! Complited in {info.elapsed_time:.3f} sec", end="\n\n")
