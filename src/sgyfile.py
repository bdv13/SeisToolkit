import numpy as np
from pathlib import Path
import struct

from config import hdrlen, bin_hdr, tr_hdr, fmt_dict
from geometry import compute_cumdist

class SGYFile:

    def __init__(self, file_path):
        self.name = file_path.stem
        self.path = file_path
        self.size_mb = None
        self.by_ord = None
        self.bps = None
        self.dtype = None
        self.format_desc = None
        self.tr_amount = None
        self.ds_ms = None
        self.numsmp = None
        self.trlen_ms = None
        self.smp_freq_hz = None
        self.line_len_km = None
        self.mean_step = None
        self.delay_flag = None
        self.text_hdr = None
        self.bin_hdr = {}
        self.tr_hdrs = {key: [] for key in tr_hdr}

    @staticmethod
    def unpack(byte_order, fmt, data, byte_range):
        start, end = byte_range
        return struct.unpack(byte_order + fmt, data[start:end])[0]

    def set_byte_order(self, raw_bin_hdr):
        code_be = self.unpack('>', 'H', raw_bin_hdr, (24, 26))
        code_le = self.unpack('<', 'H', raw_bin_hdr, (24, 26))

        if 1 <= code_be <= 12:
            self.by_ord = '>'
        elif 1 <= code_le <= 12:
            self.by_ord = '<'
        else:
            self.by_ord = '>'

    def read_hdrs(self, data, hdr_dict):
        return {
            name: self.unpack(self.by_ord, fmt, data, byte_range)
            for name, (byte_range, fmt) in hdr_dict.items()
        }

    def get_bps(self):
        fmt_code = self.bin_hdr['FMT_CODE']
        if fmt_code not in fmt_dict:
            raise ValueError(f'Unsupported SEG-Y format code: {fmt_code}')
        desc, self.bps, dtype = fmt_dict[self.bin_hdr['FMT_CODE']]
        dtype = np.dtype(dtype).newbyteorder(self.by_ord)
        self.dtype = np.dtype(dtype)
        self.format_desc = desc

    def read_data(self):
         with open(self.path, 'rb') as f:

            self.text_hdr = f.read(hdrlen['text_hdr'])

            raw_bin_hdr = f.read(hdrlen['bin_hdr'])
            self.set_byte_order(raw_bin_hdr)
            self.bin_hdr = self.read_hdrs(raw_bin_hdr, bin_hdr)
            self.get_bps()

            while True:
                raw_tr_hdr = f.read(hdrlen['trace_hdr'])
                if len(raw_tr_hdr) < hdrlen['trace_hdr']:
                    break

                trace_hdr = self.read_hdrs(raw_tr_hdr, tr_hdr)

                for key, value in trace_hdr.items():
                    self.tr_hdrs[key].append(value)

                f.seek(self.bps * trace_hdr['NUMSMP'], 1)

    def get_size_mb(self):
        size_mb = round(Path(self.path).stat().st_size / (1024 * 1024), 2)
        return size_mb

    def get_total_len_maxstep(self):
        cumdists, steps = compute_cumdist(self)

        try:
            line_len_km = round(max(cumdists) / 1000, 2)
            mean_step = round(sum(steps) / len(steps), 2)
        except Exception:
            mean_step = "Unknown"
            line_len_km = "Unknown"

        return line_len_km, mean_step

    def get_delay_flag(self):
        if self.tr_hdrs['RELRECT'] and sum(self.tr_hdrs['RELRECT']) != 0:
            return True
        else:
            return False

    def get_attributes(self):
        """Calculate attributes for dataset"""

        self.size_mb = self.get_size_mb()
        self.tr_amount = len(self.tr_hdrs['FFID'])
        self.dt_ms = self.bin_hdr['dt'] / 1000
        self.numsmp = self.bin_hdr['NUMSMP']
        self.trlen_ms = self.dt_ms * self.numsmp
        self.smp_freq_hz = 1 / (self.dt_ms / 1000)
        self.line_len_km, self.mean_step = self.get_total_len_maxstep()
        self.delay_flag = self.get_delay_flag()

    def process(self):
        """Process the dataset"""

        self.read_data()
        self.get_attributes()
