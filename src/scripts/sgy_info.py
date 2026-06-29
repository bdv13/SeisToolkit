import os

import pandas as pd

import stk.utils as u
from stk.config import fmt_dict, log_dict
from stk.geometry import compute_cumdist, get_geometry
from stk.io_data import sgy_input


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
    df = pd.DataFrame(columns=list(log_dict.keys()))
    df.to_excel(log_path, index=False, engine="openpyxl")
    return log_path


def write_log_file(log_file, log_path):
    """Append a log record to an Excel log file."""
    log_df = pd.read_excel(log_path)
    row = pd.Series(log_file)
    log_df = pd.concat([log_df, pd.DataFrame([row])], ignore_index=True)
    log_df.to_excel(log_path, index=False, engine="openpyxl")


@u.timer
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
        folder_path = u.select_folder()

    file_paths = u.get_paths(folder_path, formats=(".sgy", ".segy"))
    output_path = u.create_folder("output", folder_path)
    log_path = create_log_file(output_path)
    log_file = log_dict.copy()

    current_trace = 0

    for idx, file_path in enumerate(file_paths):
        dataset = sgy_input(file_path)

        log_file["Line"] = dataset.name
        log_file["Size_mb"] = u.get_size_mb(file_path)
        log_file["Traces"] = len(dataset.traces)

        trace_sol, trace_eol = trace_enum(dataset, current_trace)
        current_trace = trace_eol

        log_file["FFID_SOL"] = trace_sol
        log_file["FFID_EOL"] = trace_eol
        log_file["dt_ms"] = dataset.dt / 1000
        log_file["Length_ms"] = dataset.dt * dataset.numsmp / 1000
        log_file["Sample_Freq_hz"] = 1_000_000 / dataset.dt
        log_file["Byte_order"] = dataset.byte_order
        log_file["Format"] = fmt_dict[dataset.fmt_code][0]
        log_file["Length_km"] = compute_line_stats(dataset)[0]
        log_file["Mean_step_m"] = compute_line_stats(dataset)[1]
        log_file["Delay"] = delay_flag(dataset)

        write_log_file(log_file, log_path)


if __name__ == "__main__":
    print()
    info()
    print(f"Done! Complited in {info.elapsed_time:.3f} sec", end="\n\n")
