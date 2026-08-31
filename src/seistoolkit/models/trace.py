from datetime import datetime, timedelta
from typing import Literal

import numpy as np

from seistoolkit.config import TR_HDR_LEN, TRACE_HDRS
from seistoolkit.utils import pack


class Trace:
    """Represent a single seismic trace."""

    def __init__(
        self,
        tr_hdrs: dict,
        tr_data: np.ndarray,
    ):

        self.__dict__.update({
            hdr.lower(): value for hdr, value in tr_hdrs.items()
        })
        self.data = tr_data

    def export_data(self, byte_order: str = ">") -> bytes:
        """Return trace samples in binary format."""
        data = np.asarray(self.data, dtype=np.float32)

        if byte_order == ">":
            data = data.astype(">f4", copy=False)
        elif byte_order == "<":
            data = data.astype("<f4", copy=False)

        return data.tobytes()

    def export_hdrs(self, byte_order: str = ">") -> bytes:
        """Return trace header in binary format."""
        tr_array = bytearray(TR_HDR_LEN)

        tr_hdr = {
            parameter: getattr(self, parameter.lower(), 0)
            for parameter in TRACE_HDRS
        }

        for parameter, value in tr_hdr.items():
            (offset, _), fmt = TRACE_HDRS[parameter]

            pack(byte_order + fmt, tr_array, offset, value)

        return tr_array

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
