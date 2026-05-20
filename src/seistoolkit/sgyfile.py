import struct
from pathlib import Path

from seistoolkit.config import hdrs_len_dict, sample_format_dict


class SGYFile:

    def __init__(self, file_path):
        self.name = None
        self.path = file_path
        self.size_mb = None
        self.text_hdr = None
        self.bin_hdr = None
        self.byte_order = None
        self.sample_int_ms = None
        self.samples_per_tr = None
        self.tr_length_ms = None
        self.sample_freq_hz = None
        self.sample_format_code = None
        self.sample_format = None
        self.bytes_per_sample = None
        self.tr_hdrs = []
        self.tr_num = None

    def set_name(self):
        self.name = Path(self.path).stem

    def get_size_mb(self):
        self.size_mb = round(Path(self.path).stat().st_size / (1024 * 1024), 2)

    def get_text_hdr(self):
        with open(self.path, "rb") as f:
            self.text_hdr = f.read(hdrs_len_dict["text_hdr"])

    def get_bin_hdr(self):
        with open(self.path, "rb") as f:
            f.seek(hdrs_len_dict["text_hdr"])
            self.bin_hdr = f.read(hdrs_len_dict["bin_hdr"])

    def get_byte_order(self):
        code_be = struct.unpack(">H", self.bin_hdr[24:26])[0]
        code_le = struct.unpack("<H", self.bin_hdr[24:26])[0]
        if 1 <= code_be <= 12:
            self.byte_order = ">"
        elif 1 <= code_le <= 12:
            self.byte_order = "<"
        else:
            print("Warning! Cannot determine byte order.")
            self.byte_order = ">"

    def get_sample_int_ms(self):
        sample_int_us = struct.unpack(
            self.byte_order + "H", self.bin_hdr[16:18]
        )[0]
        self.sample_int_ms = sample_int_us / 1000

    def get_samples_per_trace(self):
        self.samples_per_tr = struct.unpack(
            self.byte_order + "H", self.bin_hdr[20:22]
        )[0]

    def get_trace_length_ms(self):
        self.tr_length_ms = self.sample_int_ms * self.samples_per_tr

    def get_sample_frequency_hz(self):
        self.sample_freq_hz = 1 / (self.sample_int_ms / 1000)

    def get_sample_format_code(self):
        self.sample_format_code = struct.unpack(
            self.byte_order + "H", self.bin_hdr[24:26]
        )[0]

    def get_sample_format(self):
        (sample_format,) = sample_format_dict.get(
            self.sample_format_code, ("Unknown sample format",)
        )
        self.sample_format = sample_format

    def get_bytes_per_sample(self):
        self.bytes_per_sample = sample_format_dict.get(
            self.sample_format_code, (None, None)
        )[1]

    def get_tr_hdrs(self):
        with open(self.path, "rb") as f:
            f.seek(hdrs_len_dict["text_hdr"] + hdrs_len_dict["bin_hdr"])
            while True:
                trace_hdr = f.read(hdrs_len_dict["trace_hdr"])
                if not trace_hdr:
                    break
                self.tr_hdrs.append(trace_hdr)

    def get_tr_num(self):
        self.tr_num = len(self.tr_hdrs)
