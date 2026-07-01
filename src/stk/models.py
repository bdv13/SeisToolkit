from datetime import datetime, timedelta
import numpy as np

from stk.config import bin_dict, hdrlen, tr_dict
from stk.utils import pack


class Trace:
    """Represent a single seismic trace."""

    def __init__(self, tr_hdr, tr_data):
        self.__dict__.update({k.lower(): v for k, v in tr_hdr.items()})
        self.data = tr_data

    def export_tr_hdr(self, byte_order=">"):
        """Return trace header in binary format."""
        tr_array = bytearray(hdrlen["trace_hdr"])

        tr_hdr = {
            parameter: getattr(self, parameter.lower(), 0) for parameter in tr_dict
        }

        for parameter, value in tr_hdr.items():
            (offset, _), fmt = tr_dict[parameter]

            pack(byte_order + fmt, tr_array, offset, value)

        return tr_array

    def export_tr_data(self, byte_order=">"):
        """Return trace samples in IEEE float32 format."""
        data = np.asarray(self.data, dtype=np.float32)

        if byte_order == ">":
            data = data.astype(">f4", copy=False)
        elif byte_order == "<":
            data = data.astype("<f4", copy=False)

        return data.tobytes()

    def zero_pad(self, num_samples: int, side: str = "end"):
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

    def clip(self, num_samples: int):
        """Remove samples from the end of trace."""
        if num_samples < 0:
            raise ValueError("num_samples must be >= 0")

        if num_samples > len(self.data):
            raise ValueError("num_samples exceeds trace length")

        if num_samples:
            self.data = self.data[:-num_samples]

        self.numsmp = len(self.data)

    def get_datetime(self):
        """Return trace datetime object from headers."""
        try:
            return datetime(self.year, 1, 1) + timedelta(
                days=self.day - 1,
                hours=self.hour,
                minutes=self.minute,
                seconds=self.second
            )
        except Exception:
            return datetime.min


class Dataset:
    """Represent a SEG-Y dataset."""

    def __init__(self, name, text_hdr, byte_order, dt, numsmp, traces):
        self.name = name
        self.text_hdr = text_hdr
        self.byte_order = byte_order
        self.dt = dt
        self.numsmp = numsmp
        self.fmt_code = 5
        self.traces = traces

    def export_text_hdr(self):
        """Return textual header in binary format."""
        return self.text_hdr

    def export_bin_hdr(self, **kwargs):
        """Return binary header in binary format."""

        bin_array = bytearray(hdrlen["bin_hdr"])

        bin_hdr = {
            parameter: getattr(self, parameter.lower(), 0) for parameter in bin_dict
        }

        for key in kwargs:
            if key not in bin_dict:
                raise KeyError(f"Unknown binary header field: {key}")

        bin_hdr.update(kwargs)

        for parameter, value in bin_hdr.items():
            (offset, _), fmt = bin_dict[parameter]

            pack(self.byte_order + fmt, bin_array, offset, value)

        return bin_array

    def zero_pad(self, num_samples: int, side: str = "end"):
        """Add zero samples to all traces."""
        if num_samples < 0:
            raise ValueError("num_samples must be >= 0")

        for trace in self.traces:
            trace.zero_pad(num_samples, side)

        self.numsmp = self.traces[0].numsmp

    def clip(self, num_samples: int):
        """Remove samples from the end of all traces."""
        if num_samples < 0:
            raise ValueError("num_samples must be >= 0")

        if not self.traces:
            raise ValueError("Dataset has no traces")

        if num_samples > self.traces[0].numsmp:
            raise ValueError("num_samples exceeds trace length")

        for trace in self.traces:
            trace.clip(num_samples)

        self.numsmp = self.traces[0].numsmp

    def to_section(self, transpose: bool = True) -> np.ndarray:
        """Return traces as a 2D NumPy array."""
        section = np.stack([trace.data for trace in self.traces])

        return section.T if transpose else section

    def record_length(self, value: float, unit: str = "ms"):
        """Set record length for all traces."""
        if unit == "ms":
            target_samples = int(round(value * 1000 / self.dt))
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

