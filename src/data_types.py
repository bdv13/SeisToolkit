from config import hdrlen, bin_dict


class Trace():

    def __init__(self, tr_hdr, tr_data):
        self.data = tr_data
        self.__dict__.update({k.lower(): v for k, v in tr_hdr.items()})


class Dataset():

    def __init__(self, name, text_hdr, byte_order, fmt_code, dt, numsmp, traces):
        self.name = name
        self.text_hdr = text_hdr
        self.byte_order = byte_order
        self.dt = dt
        self.numsmp = numsmp
        self.fmt_code = fmt_code
        self.traces = traces

        @staticmethod
        def create_text_hdr(text=None) -> bytes:
            if not text:
                return bytearray(hdrlen['text_hdr'])

        @staticmethod
        def create_bin_hdr(**kwargs) -> dict:

            bin_hdr = {}
            for parameter in bin_dict:
                if parameter not in kwargs:
                    bin_hdr[parameter] = 0
                else:
                    bin_hdr[parameter] = kwargs[parameter]

            return bin_hdr

