import csv
from pathlib import Path

import numpy as np

from stk.config import BIN_DICT, TR_DICT
from stk.utils import pack

BIN_HDR_LEN = 400


def get_text_enc(data: bytes) -> str:
    """
    Detect whether SEG-Y text header is encoded in ASCII or EBCDIC (cp500).
    """

    def score(s: str) -> float:
        if not s:
            return 0.0
        printable = sum(c.isprintable() or c in "\r\n\t" for c in s)
        bad = s.count("\ufffd")
        return (printable - bad * 2) / len(s)

    ascii_txt = data.decode("ascii", errors="replace")
    ebcdic_txt = data.decode("cp500", errors="replace")

    return "cp500" if score(ebcdic_txt) > score(ascii_txt) else "ascii"


def format_text_hdr(text: str) -> str:
    """Format 3200-char SEG-Y text header into 40 lines of 80 characters."""
    text = text.replace("\ufffd", " ")
    return "\n".join(text[i : i + 80].ljust(80) for i in range(0, 3200, 80))


def unformat_text_hdr(text: str) -> str:
    """Convert 40-line SEG-Y text header into a 3200-character string."""
    lines = text.splitlines()[:40]
    lines += [""] * (40 - len(lines))
    return "".join(line[:80].ljust(80) for line in lines)


def create_text_hdr(text: str | None = None, encoding: str = "cp500") -> bytes:
    """Create text header encoded as 3200 bytes in the specified encoding."""
    text = "" if text is None else text
    return unformat_text_hdr(text).encode(encoding)


def create_bin_hdr(byte_order=">", **kwargs) -> bytes:
    """Create SEG-Y binary header as 400 bytes."""
    for key in kwargs:
        if key not in BIN_DICT:
            raise KeyError(f"Unknown binary header field: {key}")

    bin_hdr = {key: 0 for key in BIN_DICT}
    bin_hdr.update(kwargs)

    bin_array = bytearray(BIN_HDR_LEN)

    for parameter, value in bin_hdr.items():
        (offset, _), fmt = BIN_DICT[parameter]
        pack(byte_order + fmt, bin_array, offset, value)

    return bytes(bin_array)


def hdr_enumerator(dataset, hdr: str, start: int = 1, step: int = 1):
    """Assign sequential values to a trace header field."""
    hdr = hdr.lower()
    if not hasattr(dataset.traces[0], hdr):
        raise ValueError(f"Unknown header: {hdr}")
    value = start
    for trace in dataset.traces:
        setattr(trace, hdr, value)
        value += step


def hdr_averager(dataset, hdr: str, window: int) -> None:
    """Apply moving average to a trace header."""
    hdr = hdr.lower()

    if window < 1:
        raise ValueError("window must be >= 1")
    if window % 2 == 0:
        window += 1

    if not hasattr(dataset.traces[0], hdr):
        raise ValueError(f"Unknown header: {hdr}")

    values = np.array([getattr(trace, hdr) for trace in dataset.traces], dtype=float)

    pad = window // 2
    padded = np.pad(values, (pad, pad), mode="edge")

    kernel = np.ones(window, dtype=float) / window
    averaged = np.convolve(padded, kernel, mode="valid")

    for trace, value in zip(dataset.traces, averaged):
        setattr(trace, hdr, value)


def hdrs_export(dataset, output_path, hdrs: tuple) -> None:
    """Export dataset trace headers in txt file."""
    for hdr in hdrs:
        if hdr.upper() not in TR_DICT:
            raise ValueError(f"Unknown header {hdr}")

    if len(dataset.traces) == 0:
        raise ValueError("Empty dataset. No trace found!")

    with open(output_path, "w", encoding="utf-8") as f:

        f.write(" ".join([hdr.upper() for hdr in hdrs]) + "\n")

        for trace in dataset.traces:
            values = (str(trace.__dict__[hdr.lower()]) for hdr in hdrs)
            f.write(" ".join(values) + "\n")


def hdrs_import(
        dataset,
        file_path: Path,
        headers: tuple[str],
        columns: tuple[int],
        match_header: str ='FFID',
        match_column: int = 0,
        cols_separator: str = ' '
) -> None:
    """Insert data from txt file into trace headers."""
    if not dataset.traces:
        raise ValueError("Dataset contains no traces.")

    if len(headers) != len(columns):
        raise ValueError("Amount of headers and columns must be equal!")

    for hdr in headers:
        if not hasattr(dataset.traces[0], hdr.lower()):
            raise AttributeError(f"Traces don't have this header {hdr}.")

    if match_header.upper() not in TR_DICT:
        raise AttributeError(f"Unknown match header {match_header}!")

    match_header = match_header.lower()
    data = {}

    invalid_lines = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=cols_separator, skipinitialspace=True)

        for line in reader:
            try:
                values = [float(line[col]) for col in columns]
                data[int(line[match_column])] = values
            except (ValueError, IndexError):
                invalid_lines += 1

    missing = 0
    for trace in dataset.traces:
        key = getattr(trace, match_header)
        values = data.get(key)

        if values is None:
            missing += 1
            continue

        for hdr, value in zip(headers, values):
            setattr(trace, hdr.lower(), value)

    if invalid_lines:
        print(f"Skipped {invalid_lines} invalid input lines.")

    if missing:
        print(f"{missing} traces were not matched by {match_header}.")
