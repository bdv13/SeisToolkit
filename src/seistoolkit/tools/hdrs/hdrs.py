from typing import BinaryIO

from seistoolkit.config import (
    BIN_HDR_LEN,
    BIN_HDRS,
    TEXT_HDR_LEN,
    TR_HDR_LEN,
    TRACE_HDRS,
)
from seistoolkit.utils import pack, unpack


def format_text_hdr(text: str) -> str:
    """Format 3200-char SEG-Y text header into 40 lines of 80 characters."""
    text = text.replace("\ufffd", " ")
    return "\n".join(text[i : i + 80].ljust(80) for i in range(0, 3200, 80))


def unformat_text_hdr(text: str) -> str:
    """Convert 40-line SEG-Y text header into a 3200-character string."""
    lines = text.splitlines()[:40]
    lines += [""] * (40 - len(lines))
    return "".join(line[:80].ljust(80) for line in lines)


def get_text_enc(data: bytes) -> str:
    """Detect if SEG-Y text header is encoded in ASCII or EBCDIC (cp500)."""

    def score(s: str) -> float:
        if not s:
            return 0.0
        printable = sum(c.isprintable() or c in "\r\n\t" for c in s)
        bad = s.count("\ufffd")
        return (printable - bad * 2) / len(s)

    ascii_txt = data.decode("ascii", errors="replace")
    ebcdic_txt = data.decode("cp500", errors="replace")

    return "cp500" if score(ebcdic_txt) > score(ascii_txt) else "ascii"


def read_text_hdr(stream: BinaryIO) -> str:
    """Read and format SEG-Y textual header."""
    raw_text_hdr = stream.read(TEXT_HDR_LEN)
    enc = get_text_enc(raw_text_hdr)
    return format_text_hdr(raw_text_hdr.decode(enc))


def create_text_hdr(text: str | None = None, encoding: str = "cp500") -> bytes:
    """Create SEG-Y textual header as 3200 bytes in the specified encoding."""
    text = "" if text is None else text
    return unformat_text_hdr(text).encode(encoding)


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


def read_bin_hdr(stream: BinaryIO) -> tuple[dict, str]:
    """Read and parse SEG-Y binary header."""
    raw_hdr = stream.read(BIN_HDR_LEN)
    byte_order = get_byte_order(raw_hdr)
    bin_hdr = parse_hdrs(raw_hdr, byte_order, BIN_HDRS)
    return bin_hdr, byte_order


def create_bin_hdr(byte_order=">", **kwargs) -> bytes:
    """Create SEG-Y binary header as 400 bytes."""
    for key in kwargs:
        if key not in BIN_HDRS:
            raise KeyError(f"Unknown binary header field: {key}")

    bin_hdr = {key: 0 for key in BIN_HDRS}
    bin_hdr.update(kwargs)

    bin_array = bytearray(BIN_HDR_LEN)

    for parameter, value in bin_hdr.items():
        (offset, _), fmt = BIN_HDRS[parameter]
        pack(byte_order + fmt, bin_array, offset, value)

    return bytes(bin_array)


def read_tr_hdr(stream: BinaryIO, byte_order: str) -> dict | None:
    """Read and parse SEG-Y trace header."""
    raw_hdr = stream.read(TR_HDR_LEN)
    if len(raw_hdr) != TR_HDR_LEN:
        return None
    return parse_hdrs(raw_hdr, byte_order, TRACE_HDRS)
