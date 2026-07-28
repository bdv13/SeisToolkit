import os
from pathlib import Path
from typing import BinaryIO

import numpy as np

from stk.config import (
    BIN_DICT,
    BIN_HDR_LEN,
    FMT_DICT,
    TEXT_HDR_LEN,
    TR_DICT,
    TR_HDR_LEN,
)
from stk.headers import format_text_hdr, get_text_enc
from stk.models import Dataset, Trace
from stk.utils import unpack


def get_byte_order(bin_hdr: bytes) -> str:
    """Determine SEG-Y byte order from format code."""
    code_be = unpack(">", "H", bin_hdr, (24, 26))
    code_le = unpack("<", "H", bin_hdr, (24, 26))

    if 1 <= code_be <= 12:
        byte_order = ">"
    elif 1 <= code_le <= 12:
        byte_order = "<"
    else:
        byte_order = ">"
    return byte_order


def parse_hdrs(data: bytes, byte_order: str, hdr_dict: dict) -> dict:
    """Parse SEG-Y header bytes into a dictionary."""
    return {
        name: unpack(byte_order, fmt, data, byte_range)
        for name, (byte_range, fmt) in hdr_dict.items()
    }


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
        return np.frombuffer(raw_tr, dtype=byte_order + "i4").astype(np.float32)
    elif fmt_code == 3:
        return np.frombuffer(raw_tr, dtype=byte_order + "i2").astype(np.float32)
    elif fmt_code == 1:
        ibm = np.frombuffer(raw_tr, dtype=">u4")
        return ibm_to_ieee(ibm)
    else:
        raise ValueError(f"Unsupported format: {fmt_code}")


def _read_text_hdr(stream: BinaryIO) -> str:
    """Read and format SEG-Y textual header."""
    raw_hdr = stream.read(TEXT_HDR_LEN)
    encoding = get_text_enc(raw_hdr)
    return format_text_hdr(raw_hdr.decode(encoding))


def _read_bin_hdr(stream: BinaryIO) -> tuple[dict, str]:
    """Read and parse SEG-Y binary header."""
    raw_hdr = stream.read(BIN_HDR_LEN)
    byte_order = get_byte_order(raw_hdr)
    bin_hdr = parse_hdrs(raw_hdr, byte_order, BIN_DICT)
    return bin_hdr, byte_order


def _get_bps(fmt_code: int) -> int:
    """Get bytes per sample (bps) value."""
    if fmt_code not in FMT_DICT:
        raise ValueError(f"Unsupported SEG-Y format code: {fmt_code}")
    return FMT_DICT[fmt_code][1]


def _read_trace_hdr(stream: BinaryIO, byte_order: str) -> dict | None:
    """Read and parse SEG-Y trace header."""
    raw_hdr = stream.read(TR_HDR_LEN)
    if len(raw_hdr) != TR_HDR_LEN:
        return None
    return parse_hdrs(raw_hdr, byte_order, TR_DICT)


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
    file_path: Path, headers_only: bool = False, normalize_hdrs: bool = True
) -> Dataset:
    """Read a SEG-Y file and return a dataset object."""

    file_name = file_path.stem

    with open(file_path, "rb") as sgy_file:
        text_hdr = _read_text_hdr(sgy_file)
        bin_hdr, byte_order = _read_bin_hdr(sgy_file)

        fmt_code = bin_hdr["FMT_CODE"]
        bps = _get_bps(fmt_code)

        traces = []
        while True:
            tr_hdr = _read_trace_hdr(sgy_file, byte_order)
            if tr_hdr is None:
                break

            num_bytes = bps * tr_hdr["NUMSMP"]

            if headers_only:
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
            file_name, text_hdr, byte_order, bin_hdr["dt_us"], bin_hdr["NUMSMP"], traces
        )

        if not headers_only and normalize_hdrs:
            dataset.norm_hdrs()

        return dataset


def sgy_output(
    dataset: Dataset,
    output_path: Path,
    sac: int = 1,
    saed: int = 1,
    text_hdr: str | None = None,
    bin_hdr: dict | None = None,
) -> None:
    """Export dataset object to standard SEG-Y file."""

    dataset.denorm_hdrs(sac=sac, saed=saed)

    try:
        with open(output_path, "wb") as f:
            f.write(dataset.export_text_hdr(text_hdr))
            f.write(dataset.export_bin_hdr(**(bin_hdr or {})))

            for trace in dataset.traces:
                f.write(trace.export_tr_hdr(dataset.byte_order))
                f.write(trace.export_tr_data(dataset.byte_order))

    finally:
        dataset.norm_hdrs()
