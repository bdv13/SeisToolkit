from stk.config import hdrlen, bin_dict, tr_dict
from stk.utils import pack


def get_text_enc(data: bytes) -> str:
    """
    Detect whether SEG-Y text header is encoded in ASCII or EBCDIC (cp500).
    """
    def score(s: str) -> float:
        if not s:
            return 0.0
        printable = sum(c.isprintable() or c in "\r\n\t" for c in s)
        bad = s.count("\ufffd")
        return (printable - bad * 2) / len(s)

    ascii_txt = data.decode("ascii", errors="replace")
    ebcdic_txt = data.decode("cp500", errors="replace")

    return "cp500" if score(ebcdic_txt) > score(ascii_txt) else "ascii"


def format_text_hdr(text: str) -> str:
    """Format 3200-char SEG-Y text header into 40 lines of 80 characters."""
    text = text.replace("\ufffd", " ")

    return "\n".join(
        text[i:i+80].ljust(80)
        for i in range(0, 3200, 80)
    )


def unformat_text_hdr(text: str) -> str:
    """Convert 40-line SEG-Y text header into a 3200-character string."""
    lines = text.splitlines()[:40]
    lines += [''] * (40 - len(lines))

    return ''.join(
        line[:80].ljust(80)
        for line in lines
    )


def create_text_hdr(text: str | None = None, encoding: str ='cp500') -> bytes:
    """
    Create SEG-Y text header encoded as 3200 bytes in the specified encoding.
    """
    text = '' if text is None else text
    return unformat_text_hdr(text).encode(encoding)


def create_bin_hdr(byte_order='>', **kwargs) -> bytes:
    """Create SEG-Y binary header as 400 bytes."""
    for key in kwargs:
        if key not in bin_dict:
            raise KeyError(f"Unknown binary header field: {key}")

    bin_array = bytearray(hdrlen['bin_hdr'])

    bin_hdr = {key: 0 for key in bin_dict}
    bin_hdr.update(kwargs)

    for parameter, value in bin_hdr.items():

        (offset, _), fmt = bin_dict[parameter]

        pack(
            byte_order + fmt,
            bin_array,
            offset,
            value
        )

    return bin_array


def hdr_enumerator(dataset, header: str, start: int = 1, step: int = 1):
    """Assign sequential values to a trace header field."""
    header = header.lower()
    if not hasattr(dataset.traces[0], header):
            raise ValueError(f"Unknown header: {header}")
    value = start
    for trace in dataset.traces:
        setattr(trace, header, value)
        value += step


def export_hdrs(dataset, output_path, hdrs):
    """Export dataset trace headers in txt file."""
    for hdr in hdrs:
        if hdr.upper() not in tr_dict:
            raise ValueError(f"Unknown header {hdr}")
    if len(dataset.traces) == 0:
            raise ValueError("Empty dataset. No trace found!")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(" ".join([hdr.upper() for hdr in hdrs]) + "\n")
        for trace in dataset.traces:
            values = (str(trace.__dict__[hdr.lower()]) for hdr in hdrs)
            f.write(" ".join(values) + "\n")
