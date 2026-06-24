from pathlib import Path

import numpy as np

from stk.config import bin_dict, fmt_dict, hdrlen, tr_dict
from stk.models import Dataset, Trace
from stk.utils import unpack


def get_byte_order(bin_hdr: bytes) -> str:
    """
    Determine SEG-Y byte order from format code.
    Returns '>' for big-endian or '<' for little-endian.
    """

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

    sign = (arr >> 31) & 0x01
    exponent = (arr >> 24) & 0x7F
    mantissa = arr & 0x00FFFFFF
    out = np.zeros_like(arr, dtype=np.float32)
    mask = arr != 0
    out[mask] = (mantissa[mask] / 0x1000000) * (16 ** (exponent[mask] - 64))
    out[mask] *= np.where(sign[mask] == 1, -1.0, 1.0)
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


def sgy_input(file_path: Path) -> Dataset:
    """Read a SEG-Y file and return a Dataset object."""

    with open(file_path, "rb") as f:
        name = Path(file_path).stem

        text_hdr = f.read(hdrlen["text_hdr"])

        raw_bin_hdr = f.read(hdrlen["bin_hdr"])
        byte_order = get_byte_order(raw_bin_hdr)
        bin_hdr = parse_hdrs(raw_bin_hdr, byte_order, bin_dict)

        fmt_code = bin_hdr["FMT_CODE"]
        if fmt_code not in fmt_dict:
            raise ValueError(f"Unsupported SEG-Y format code: {fmt_code}")
        bps = fmt_dict[fmt_code][1]

        dt = bin_hdr["dt"]
        numsmp = bin_hdr["NUMSMP"]

        traces = []
        while True:
            raw_tr_hdr = f.read(hdrlen["trace_hdr"])
            if len(raw_tr_hdr) < hdrlen["trace_hdr"]:
                break
            tr_hdr = parse_hdrs(raw_tr_hdr, byte_order, tr_dict)

            numsmp = tr_hdr["NUMSMP"]
            raw_data = f.read(bps * numsmp)
            if len(raw_data) < bps * numsmp:
                break
            tr_data = decode_trace(raw_data, fmt_code, byte_order)

            traces.append(Trace(tr_hdr, tr_data))

    return Dataset(name, text_hdr, byte_order, dt, numsmp, traces)


def sgy_output(dataset: Dataset, output_path: Path) -> bytes:
    """Export dataset to SEG-Y file."""

    with open(output_path, "wb") as f:
        # headers
        f.write(dataset.export_text_hdr())
        f.write(dataset.get_bin_hdr())

        # traces
        for trace in dataset.traces:
            f.write(trace.get_tr_hdr(dataset.byte_order))
            f.write(trace.get_tr_data(dataset.byte_order))
