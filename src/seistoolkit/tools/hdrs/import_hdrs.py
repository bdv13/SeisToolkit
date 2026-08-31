import csv
from pathlib import Path

from seistoolkit.config import TRACE_HDRS
from seistoolkit.models import Dataset


def import_hdrs(
    dataset: Dataset,
    file_path: Path,
    hdrs: tuple[str, ...],
    cols: tuple[int, ...],
    cols_sep: str = " ",
    match_col: int = 0,
    match_hdr: str = "FFID",
) -> None:
    """Insert data from txt file into trace headers."""

    if not dataset.traces:
        raise ValueError("Dataset contains no traces.")

    if len(hdrs) != len(cols):
        raise ValueError("Amount of headers and columns must be equal!")

    for hdr in hdrs:
        if not hasattr(dataset.traces[0], hdr.lower()):
            raise AttributeError(f"Traces don't have this header {hdr}.")

    if match_hdr.upper() not in TRACE_HDRS:
        raise AttributeError(f"Unknown match header {match_hdr}!")

    match_hdr = match_hdr.lower()
    data = {}

    invalid_lines = 0
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=cols_sep, skipinitialspace=True)

        for line in reader:
            try:
                values = [float(line[col]) for col in cols]
                data[int(line[match_col])] = values
            except ValueError, IndexError:
                invalid_lines += 1

    missing = 0
    for trace in dataset.traces:
        key = getattr(trace, match_hdr)
        values = data.get(key)

        if values is None:
            missing += 1
            continue

        for hdr, value in zip(hdrs, values):
            setattr(trace, hdr.lower(), value)

    if invalid_lines:
        print(f"Skipped {invalid_lines} invalid input lines.")

    if missing:
        print(f"{missing} traces were not matched by {match_hdr}.")
