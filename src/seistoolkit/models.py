import csv
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

import numpy as np

from seistoolkit.config import (
    BIN_DICT,
    ELEV_COORD_PRECISION,
    READ_ONLY_BIN_HDRS,
    SCALED_HDRS,
    TR_DICT,
    TR_HDR_LEN,
)
from seistoolkit.headers import create_bin_hdr, create_text_hdr
from seistoolkit.utils import pack


def _round(value: float, prec: int = ELEV_COORD_PRECISION) -> float:
    return round(value, prec)


def _scalar(value: int) -> float:
    if value > 0:
        return value
    if value < 0:
        return 1 / abs(value)
    return 1


class Dataset:
    """Represent a SEG-Y dataset."""

    def __init__(
        self,
        name: str,
        text_hdr: str,
        byte_order: str,
        dt: int,
        numsmp: int,
        traces: list["Trace"],
    ):
        self.name = name
        self.text_hdr = text_hdr
        self.byte_order = byte_order
        self.dt_us = dt
        self.numsmp = numsmp
        self.fmt_code = 5
        self.traces = traces

    def norm_hdrs(self) -> None:
        """Apply SAC and SAED to coordinates and elevations."""
        for trace in self.traces:
            for scale_hdr, hdrs in SCALED_HDRS.items():
                raw = getattr(trace, scale_hdr)
                coeff = _scalar(raw)

                for hdr in hdrs:
                    value = getattr(trace, hdr)
                    scaled = value * coeff
                    setattr(trace, hdr, _round(scaled))

                setattr(trace, scale_hdr, 1)

    def denorm_hdrs(self, sac: int = 1, saed: int = 1) -> None:
        """Prepare coordinates and elevations for SEG-Y export."""
        coeffs = {
            "sac": (sac, _scalar(sac)),
            "saed": (saed, _scalar(saed)),
        }

        for trace in self.traces:
            for scale_hdr, hdrs in SCALED_HDRS.items():
                raw_coeff, coeff = coeffs[scale_hdr]

                for hdr in hdrs:
                    value = getattr(trace, hdr) / coeff
                    setattr(trace, hdr, int(round(value)))

                setattr(trace, scale_hdr, raw_coeff)

    def export_text_hdr(self, text_hdr: str | None = None) -> bytes:
        """Return textual header in binary format."""
        text = self.text_hdr if text_hdr is None else text_hdr
        return create_text_hdr(text)

    def export_bin_hdr(self, **kwargs) -> bytes:
        """Return binary header in binary format."""
        for key in kwargs:
            if key.lower() in READ_ONLY_BIN_HDRS:
                raise ValueError(
                    f"Binary header field '{key}' is read-only and "
                    "must be taken from Dataset"
                )

        bin_hdr = {
            parameter: getattr(self, parameter.lower(), 0)
            for parameter in BIN_DICT
        }

        bin_hdr.update(kwargs)

        return create_bin_hdr(byte_order=self.byte_order, **bin_hdr)

    def set_hdr(self, headers: dict[str, float]) -> None:
        """Set header values for all traces."""
        headers = {hdr.lower(): value for hdr, value in headers.items()}

        for hdr in headers:
            if hdr.upper() not in TR_DICT:
                raise ValueError(f"Unknown header {hdr}")

        for trace in self.traces:
            for hdr, value in headers.items():
                setattr(trace, hdr, value)

    def copy_hdr(self, hdr: str, hdrs: str | list[str]) -> None:
        """Copy header value to one or multiple headers."""
        hdr = hdr.lower()
        if isinstance(hdrs, str):
            hdrs = [hdrs]
        hdrs = [h.lower() for h in hdrs]

        headers = [hdr] + hdrs

        for h in headers:
            if h.upper() not in TR_DICT:
                raise ValueError(f"Unknown header {h}")

        for trace in self.traces:
            value = getattr(trace, hdr)

            for h in hdrs:
                setattr(trace, h, value)

    def zero_pad(
        self, num_samples: int, side: Literal["start", "end"] = "end"
    ) -> None:
        """Add zero samples to all traces."""
        if num_samples < 0:
            raise ValueError("num_samples must be >= 0")

        if not self.traces:
            raise ValueError("Dataset has no traces")

        for trace in self.traces:
            trace.zero_pad(num_samples, side)

        self.numsmp = self.traces[0].numsmp

    def clip(
        self, num_samples: int, side: Literal["start", "end"] = "end"
    ) -> None:
        """Remove samples from the beginning or end of all traces."""
        if num_samples < 0:
            raise ValueError("num_samples must be >= 0")

        if not self.traces:
            raise ValueError("Dataset has no traces")

        if num_samples > self.traces[0].numsmp:
            raise ValueError("num_samples exceeds trace length")

        for trace in self.traces:
            trace.clip(num_samples, side)

        self.numsmp = self.traces[0].numsmp

    def record_length(
        self, value: float, unit: Literal["ms", "samples"] = "ms"
    ) -> None:
        """Set record length for all traces."""
        if unit == "ms":
            target_samples = int(round(value * 1000 / self.dt_us))
        else:
            target_samples = int(value)

        if target_samples < 0:
            raise ValueError("record length must be >= 0")

        if self.numsmp < target_samples:
            self.zero_pad(target_samples - self.numsmp)
        elif self.numsmp > target_samples:
            self.clip(self.numsmp - target_samples)

    def sort_traces(self, *headers: str, reverse: bool = False) -> None:
        """Sort traces by one or more trace header fields."""
        keys = [h.lower() for h in headers]

        def key_fn(tr):
            return tuple(getattr(tr, h, 0) for h in keys)

        self.traces.sort(key=key_fn, reverse=reverse)

    def filter_traces(self, hdr: str, value, include: bool = False) -> None:
        """Keep or remove traces matching a header value."""
        hdr = hdr.lower()

        if hdr.upper() not in TR_DICT:
            raise ValueError(f"Unknown header {hdr}.")

        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            values = set(value)

            def match(trace):
                return getattr(trace, hdr) in values
        else:

            def match(trace):
                return getattr(trace, hdr) == value

        self.traces = [tr for tr in self.traces if match(tr) == include]

    @property
    def section(self) -> np.ndarray:
        """Return seismic section (samples - traces)."""
        if not self.traces:
            raise ValueError("Dataset contains no traces.")

        return np.stack([trace.data for trace in self.traces]).T

    def trace_data(self) -> np.ndarray:
        """Return trace data (traces - samples)."""
        if not self.traces:
            raise ValueError("Dataset contains no traces.")

        return np.stack([trace.data for trace in self.traces])

    def set_section(self, section: np.ndarray) -> None:
        """Replace trace data from a seismic section."""
        if section.ndim != 2:
            raise ValueError("Section must be a 2D NumPy array.")

        if section.shape != (self.numsmp, len(self.traces)):
            raise ValueError("Section shape does not match the dataset.")

        for trace, data in zip(self.traces, section.T):
            trace.data = data.copy()

    @property
    def nyquist(self) -> float:
        """Return Nyquist frequency."""
        return 1_000_000 / (2 * self.dt_us)


class Trace:
    """Represent a single seismic trace."""

    def __init__(self, tr_hdr, tr_data):
        self.__dict__.update({k.lower(): v for k, v in tr_hdr.items()})
        self.data = tr_data

    def export_tr_hdr(self, byte_order: str = ">") -> bytearray:
        """Return trace header in binary format."""
        tr_array = bytearray(TR_HDR_LEN)

        tr_hdr = {
            parameter: getattr(self, parameter.lower(), 0)
            for parameter in TR_DICT
        }

        for parameter, value in tr_hdr.items():
            (offset, _), fmt = TR_DICT[parameter]

            pack(byte_order + fmt, tr_array, offset, value)

        return tr_array

    def export_tr_data(self, byte_order: str = ">") -> bytes:
        """Return trace samples in IEEE float32 format."""
        data = np.asarray(self.data, dtype=np.float32)

        if byte_order == ">":
            data = data.astype(">f4", copy=False)
        elif byte_order == "<":
            data = data.astype("<f4", copy=False)

        return data.tobytes()

    def zero_pad(
        self, num_samples: int, side: Literal["start", "end"] = "end"
    ) -> None:
        """Add zero samples to trace data."""
        if num_samples < 0:
            raise ValueError("num_samples must be >= 0")

        if side == "start":
            self.data = np.pad(self.data, (num_samples, 0))
        elif side == "end":
            self.data = np.pad(self.data, (0, num_samples))
        else:
            raise ValueError("side must be 'start' or 'end'")

        self.numsmp = len(self.data)

    def clip(
        self, num_samples: int, side: Literal["start", "end"] = "end"
    ) -> None:
        """Remove samples from the beginning or end of the trace."""
        if num_samples < 0:
            raise ValueError("num_samples must be >= 0")

        if num_samples > len(self.data):
            raise ValueError("num_samples exceeds trace length")

        if side == "end":
            self.data = self.data[:-num_samples] if num_samples else self.data
        elif side == "start":
            self.data = self.data[num_samples:]
        else:
            raise ValueError("side must be 'start' or 'end'")

        self.numsmp = len(self.data)

    def get_dt(self):
        """Return trace datetime object from headers."""
        try:
            return datetime(self.year, 1, 1) + timedelta(
                days=self.day - 1,
                hours=self.hour,
                minutes=self.minute,
                seconds=self.second,
            )
        except Exception:
            return datetime.min


@dataclass(slots=True)
class Picks:
    """Seismic picks container."""

    hdrs: dict[str, list[int]]
    twt_ms: np.ndarray

    @property
    def size(self) -> int:
        return len(self.twt_ms)

    def _validate_hdrs(self, *hdrs):
        for hdr in hdrs:
            if hdr not in self.hdrs:
                raise KeyError(f"Header '{hdr}' is not found!")
            if len(self.hdrs[hdr]) != self.size:
                raise ValueError(f"{hdr} has wrong length!")

    @staticmethod
    def import_txt(
        file_path: Path,
        hdrs_cols: tuple[int | str, ...],
        data_col: int | str,
    ) -> "Picks":
        """Create Picks from a tab-separated text file."""
        with open(file_path, newline="", encoding="utf-8-sig") as file:
            rows = csv.reader(file, delimiter="\t")
            header = next(rows, None)

            if not header:
                raise ValueError("Text file has no header")

            header = [name.strip() for name in header]
            if len(header) != len(set(header)):
                raise ValueError("Text file header contains duplicate names")

            def column_index(column: int | str) -> int:
                if isinstance(column, str):
                    try:
                        return header.index(column)
                    except ValueError as error:
                        raise ValueError(
                            f"Column '{column}' is not found"
                        ) from error

                if not 0 <= column < len(header):
                    raise ValueError(f"Column index {column} is out of range")
                return column

            hdr_indices = [column_index(column) for column in hdrs_cols]
            time_index = column_index(data_col)
            hdr_values: dict[str, list[int]] = {
                header[index]: [] for index in hdr_indices
            }
            twt_ms = []

            for line_number, row in enumerate(rows, start=2):
                if not row or not any(value.strip() for value in row):
                    continue
                if len(row) != len(header):
                    raise ValueError(
                        f"Line {line_number} has {len(row)} columns; "
                        f"expected {len(header)}"
                    )

                try:
                    for index in hdr_indices:
                        hdr_values[header[index]].append(int(row[index]))
                    twt_ms.append(float(row[time_index]))
                except ValueError as error:
                    raise ValueError(
                        f"Invalid value on line {line_number}"
                    ) from error

        return Picks(hdrs=hdr_values, twt_ms=np.asarray(twt_ms))

    def export_rdx_pick(
        self,
        hdr1: str,
        hdr2: str,
        output_path: Path,
    ) -> None:
        """Export picks to RadExPro txt format."""

        self._validate_hdrs(hdr1, hdr2)

        with open(output_path, "w", encoding="utf-8") as f:
            # write file header:
            f.write(f"{hdr1}:{hdr2}\n")

            # write values:
            for val1, val2, twt in zip(
                self.hdrs[hdr1],
                self.hdrs[hdr2],
                self.twt_ms,
            ):
                f.write(f"{val1:15d}:{val2:15d}{twt:15.4f}\n")
