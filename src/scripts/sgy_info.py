import os
import pandas as pd

import stk.utils as u
from stk.config import fmt_dict, log_dict
from stk.geometry import compute_cumdist, get_geometry
from stk.io_data import sgy_input


def delay_flag(dataset):
    delays = []
    for trace in dataset.traces:
        delays.append(trace.relrect)
    if sum(delays) == 0:
        return False
    else:
        return True


def linelen_maxstep(dataset):
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
    trace_sol = start_value + 1
    trace_eol = start_value + len(dataset.traces)
    return trace_sol, trace_eol


def create_log_file(path):
    log_path = os.path.join(path, "Log.xlsx")
    df = pd.DataFrame(columns=list(log_dict.keys()))
    df.to_excel(log_path, index=False, engine="openpyxl")
    return log_path


def write_log_file(log_file, log_path):
    log_df = pd.read_excel(log_path)
    row = pd.Series(log_file)
    log_df = pd.concat([log_df, pd.DataFrame([row])], ignore_index=True)
    log_df.to_excel(log_path, index=False, engine="openpyxl")


@u.timer
def info(folder_path=None):

    if folder_path is None:
        folder_path = u.get_folder()

    file_paths = u.get_paths(folder_path, formats=(".sgy", ".segy"))
    output_path = u.create_folder('output', folder_path)
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
        log_file["Length_km"] = linelen_maxstep(dataset)[0]
        log_file["Mean_step_m"] = linelen_maxstep(dataset)[1]
        log_file["Delay"] = delay_flag(dataset)

        write_log_file(log_file, log_path)


if __name__ == "__main__":
    print()
    info()
    print(f"Done! Complited in {info.elapsed_time:.3f} sec", end="\n\n")
