import struct
from pathlib import Path

from config import (
    bin_dict,
    hdrlen_dict,
    sample_fmt_dict,
    tr_dict,
)


class SGYFile:

    def __init__(self, file_path):
        self.name = None  # dataset name
        self._path = file_path  # dataset path
        self.size_mb = None  # dataset size (MB)
        self.text_hdr = None  # texual header
        self.bin_hdr = None  # binary header
        self.byte_order = None  # endian: '>' or '<'
        self.dt_ms = None  # sample interval (ms)
        self.ns = None  # number of samples per trace
        self.trlen_ms = None  # trace length in ms
        self.sample_freq_hz = None  # sampling frequency (Hz)
        self.fmt_code = None  # SEG-Y sample formate code (1-12)
        self.fmt_name = None  # sample format code description
        self.bps = None  # bytes per sample
        self.tr_hdrs = []  # trace headers list
        self.tr_num = None  # number of traces
        self.ffids = []  # FFID list
        self.sou_x_list = []  # source x coordinates
        self.sou_y_list = []  # sorce y coordinates
        self.sac = None  # scaling factor for sou/rec coord
        self.units = None  # coordinate units

    def get_name(self):
        self.name = Path(self._path).stem

    def get_size_mb(self):
        self.size_mb = round(Path(self._path).stat().st_size / (1024 * 1024), 2)

    def get_text_hdr(self):
        with open(self._path, "rb") as f:
            self.text_hdr = f.read(hdrlen_dict["text_hdr"])

    def get_bin_hdr(self):
        with open(self._path, "rb") as f:
            f.seek(hdrlen_dict["text_hdr"])
            self.bin_hdr = f.read(hdrlen_dict["bin_hdr"])

    def get_byte_order(self):
        start, end = bin_dict["fmt"]
        data = self.bin_hdr[start:end]
        code_be = struct.unpack(">H", data)[0]
        code_le = struct.unpack("<H", data)[0]
        if 1 <= code_be <= 12:
            self.byte_order = ">"
        elif 1 <= code_le <= 12:
            self.byte_order = "<"
        else:
            print("Warning! Cannot determine byte order.")
            self.byte_order = ">"

    def unpack_field(self, fmt, data, byte_range):
        start, end = byte_range
        return struct.unpack(self.byte_order + fmt, data[start:end])[0]

    def get_dt_ms(self):
        sample_int_us = self.unpack_field("H", self.bin_hdr, bin_dict["dt"])
        self.dt_ms = sample_int_us / 1000

    def get_ns(self):
        self.ns = self.unpack_field("H", self.bin_hdr, bin_dict["ns"])

    def get_trlen_ms(self):
        self.trlen_ms = self.dt_ms * self.ns

    def get_sample_frequency_hz(self):
        self.sample_freq_hz = 1 / (self.dt_ms / 1000)

    def get_fmt_code(self):
        self.fmt_code = self.unpack_field("H", self.bin_hdr, bin_dict["fmt"])

    def get_fmt_name(self):
        self.fmt_name = sample_fmt_dict.get(self.fmt_code, ("Unknown", None))[0]

    def get_bps(self):
        self.bps = sample_fmt_dict.get(self.fmt_code, (None, None))[1]

    def get_tr_hdrs(self):
        with open(self._path, "rb") as f:
            f.seek(hdrlen_dict["text_hdr"] + hdrlen_dict["bin_hdr"])
            while True:
                trace_hdr = f.read(hdrlen_dict["trace_hdr"])
                if not trace_hdr:
                    break
                self.tr_hdrs.append(trace_hdr)
                # TEMP: skip trace data!
                f.seek(self.ns * self.bps, 1)

    def get_tr_num(self):
        self.tr_num = len(self.tr_hdrs)

    def get_ffids(self):
        for tr_hdr in self.tr_hdrs:
            ffid = self.unpack_field("I", tr_hdr, tr_dict["ffid"])
            self.ffids.append(ffid)

    def get_geometry(self):
        for tr_hdr in self.tr_hdrs:

            self.units = self.unpack_field("H", tr_hdr, tr_dict["units"])

            raw_sac = self.unpack_field("h", tr_hdr, tr_dict["sac"])

            if raw_sac < 0:
                self.sac = 1 / abs(raw_sac)
            elif raw_sac > 0:
                self.sac = raw_sac
            else:
                self.sac = 1

            src_x = self.unpack_field("I", tr_hdr, tr_dict["sou_x"])
            src_y = self.unpack_field("I", tr_hdr, tr_dict["sou_y"])

            self.sou_x_list.append(round(src_x * self.sac, 3))
            self.sou_y_list.append(round(src_y * self.sac, 3))
