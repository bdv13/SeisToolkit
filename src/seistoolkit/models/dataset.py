from collections.abc import Iterable
from typing import Literal

import numpy as np

from seistoolkit.config import (
    BIN_HDRS,
    ELEV_COORD_PRECISION,
    READ_ONLY_BIN_HDRS,
    SCALED_TRACE_HDRS,
    TRACE_HDRS,
)

from .trace import Trace


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
            for scale_hdr, hdrs in SCALED_TRACE_HDRS.items():
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
            for scale_hdr, hdrs in SCALED_TRACE_HDRS.items():
                raw_coeff, coeff = coeffs[scale_hdr]

                for hdr in hdrs:
                    value = getattr(trace, hdr) / coeff
                    setattr(trace, hdr, int(round(value)))

                setattr(trace, scale_hdr, raw_coeff)

    def export_text_hdr(self, text_hdr: str | None = None) -> bytes:
        """Return textual header in binary format."""
        from seistoolkit.tools.hdrs import create_text_hdr

        text = self.text_hdr if text_hdr is None else text_hdr
        return create_text_hdr(text)

    def export_bin_hdr(self, **kwargs) -> bytes:
        """Return binary header in binary format."""
        from seistoolkit.tools.hdrs import create_bin_hdr

        for key in kwargs:
            if key.lower() in READ_ONLY_BIN_HDRS:
                raise ValueError(
                    f"Binary header field '{key}' is read-only and "
                    "must be taken from Dataset"
                )

        bin_hdr = {
            parameter: getattr(self, parameter.lower(), 0)
            for parameter in BIN_HDRS
        }

        bin_hdr.update(kwargs)

        return create_bin_hdr(byte_order=self.byte_order, **bin_hdr)

    def set_hdr(self, headers: dict[str, float]) -> None:
        """Set header values for all traces."""
        headers = {hdr.lower(): value for hdr, value in headers.items()}

        for hdr in headers:
            if hdr.upper() not in TRACE_HDRS:
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
            if h.upper() not in TRACE_HDRS:
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

        if hdr.upper() not in TRACE_HDRS:
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
