from pathlib import Path

import numpy as np

from stk.config import BIN_DICT, FMT_DICT, TR_DICT
from stk.models import Dataset, Trace
from stk.utils import unpack

TEXT_HDR_LEN = 3200
BIN_HDR_LEN = 400
TR_HDR_LEN = 240


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
    """Read a SEG-Y file and return a dataset object."""
    file_name = Path(file_path).stem

    with open(file_path, "rb") as f:
        # read textual reader:
        text_hdr = f.read(TEXT_HDR_LEN)

        # read binary header:
        raw_bin_hdr = f.read(BIN_HDR_LEN)
        byte_order = get_byte_order(raw_bin_hdr)
        bin_hdr = parse_hdrs(raw_bin_hdr, byte_order, BIN_DICT)

        fmt_code = bin_hdr["FMT_CODE"]

        if fmt_code not in FMT_DICT:
            raise ValueError(f"Unsupported SEG-Y format code: {fmt_code}")

        bps = FMT_DICT[fmt_code][1]

        dt = bin_hdr["dt"]
        numsmp = bin_hdr["NUMSMP"]

        # read trace data -> Trace objects:
        traces = []
        while True:
            # read trace headers:
            raw_tr_hdr = f.read(TR_HDR_LEN)
            if len(raw_tr_hdr) < TR_HDR_LEN:
                break
            tr_hdr = parse_hdrs(raw_tr_hdr, byte_order, TR_DICT)

            # read trace data:
            numsmp = tr_hdr["NUMSMP"]
            raw_data = f.read(bps * numsmp)
            if len(raw_data) < bps * numsmp:
                break
            tr_data = decode_trace(raw_data, fmt_code, byte_order)

            traces.append(Trace(tr_hdr, tr_data))

        dataset = Dataset(file_name, text_hdr, byte_order, dt, numsmp, traces)
        dataset.norm_hdrs()

    return dataset


def sgy_output(
        dataset: Dataset,
        output_path: Path,
        sac: int = 1,
        saed: int = 1
) -> None:
    """Export dataset object to standard SEG-Y file."""

    dataset.denorm_hdrs(sac=sac, saed=saed)

    try:
        with open(output_path, "wb") as f:
            f.write(dataset.export_text_hdr())
            f.write(dataset.export_bin_hdr())

            for trace in dataset.traces:
                f.write(trace.export_tr_hdr(dataset.byte_order))
                f.write(trace.export_tr_data(dataset.byte_order))

    finally:
        dataset.norm_hdrs()
