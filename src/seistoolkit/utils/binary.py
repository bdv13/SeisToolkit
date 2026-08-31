import struct
from typing import Any


def pack(fmt: str, hdr: bytearray, offset: int, value: Any) -> None:
    """Pack value into header buffer at specified offset."""
    struct.pack_into(fmt, hdr, offset, value)


def unpack(
    byte_order: str,
    fmt: str,
    data: bytes,
    byte_range: tuple[int, int],
) -> Any:
    """Extract and unpack a value from a byte sequence."""
    start, end = byte_range
    return struct.unpack(byte_order + fmt, data[start:end])[0]
