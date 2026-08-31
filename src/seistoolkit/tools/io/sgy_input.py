import os
from pathlib import Path
from typing import BinaryIO

import numpy as np

from seistoolkit.config import FMT_DICT
from seistoolkit.models import Dataset, Trace
from seistoolkit.tools.hdrs import read_bin_hdr, read_text_hdr, read_tr_hdr


def ibm_to_ieee(arr: np.ndarray) -> np.ndarray:
    """Convert IBM floating-point values to IEEE float32."""
    arr = arr.astype(np.uint32, copy=False)
    sign = (arr >> 31) & 1
    exponent = ((arr >> 24) & 0x7F).astype(np.int32)
    mantissa = arr & 0x00FFFFFF
    out = np.zeros(arr.shape, dtype=np.float64)
    mask = arr != 0
    out[mask] = (
        mantissa[mask].astype(np.float64)
        / 16777216.0
        * np.power(16.0, exponent[mask] - 64)
    )
    out[mask] *= np.where(sign[mask], -1.0, 1.0)
    return out.astype(np.float32)


def decode_trace(raw_tr: bytes, fmt_code: int, byte_order: str) -> np.ndarray:
    """Decode seismic trace samples to float32."""
    if fmt_code == 5:
        return np.frombuffer(raw_tr, dtype=byte_order + "f4")
    elif fmt_code == 2:
        return np.frombuffer(raw_tr, dtype=byte_order + "i4").astype(
            np.float32
        )
    elif fmt_code == 3:
        return np.frombuffer(raw_tr, dtype=byte_order + "i2").astype(
            np.float32
        )
    elif fmt_code == 1:
        ibm = np.frombuffer(raw_tr, dtype=">u4")
        return ibm_to_ieee(ibm)
    else:
        raise ValueError(f"Unsupported format: {fmt_code}")


def _get_bps(fmt_code: int) -> int:
    """Get bytes per sample (bps) value."""
    if fmt_code not in FMT_DICT:
        raise ValueError(f"Unsupported SEG-Y format code: {fmt_code}")
    return FMT_DICT[fmt_code][1]


def _read_trace_data(
    stream: BinaryIO,
    byte_order: str,
    fmt_code: int,
    num_bytes: int,
) -> np.ndarray | None:
    """Read and decode SEG-Y trace data."""
    raw_data = stream.read(num_bytes)
    if len(raw_data) != num_bytes:
        return None
    return decode_trace(raw_data, fmt_code, byte_order)


def sgy_input(
    file_path: Path,
    hdrs_only: bool = False,
    norm_hdrs: bool = True,
) -> Dataset:
    """Read a SEG-Y file and return a dataset object."""

    file_name = file_path.stem

    with open(file_path, "rb") as sgy_file:
        text_hdr = read_text_hdr(sgy_file)
        bin_hdr, byte_order = read_bin_hdr(sgy_file)

        fmt_code = bin_hdr["FMT_CODE"]
        bps = _get_bps(fmt_code)

        traces = []
        while True:
            tr_hdr = read_tr_hdr(sgy_file, byte_order)
            if tr_hdr is None:
                break

            num_bytes = bps * tr_hdr["NUMSMP"]

            if hdrs_only:
                sgy_file.seek(num_bytes, os.SEEK_CUR)
                tr_data = None

            else:
                tr_data = _read_trace_data(
                    sgy_file,
                    byte_order,
                    fmt_code,
                    num_bytes,
                )

                if tr_data is None:
                    raise EOFError("Unexpected end of SEG-Y trace data.")

            traces.append(Trace(tr_hdr, tr_data))

        dataset = Dataset(
            file_name,
            text_hdr,
            byte_order,
            bin_hdr["dt_us"],
            bin_hdr["NUMSMP"],
            traces,
        )

        if not hdrs_only and norm_hdrs:
            dataset.norm_hdrs()

        return dataset
