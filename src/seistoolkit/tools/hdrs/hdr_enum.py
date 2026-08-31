from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from seistoolkit.models import Dataset


def hdr_enum(dataset: "Dataset", hdr: str, start: int = 1, step: int = 1):
    """Assign sequential values to a trace header field."""

    hdr = hdr.lower()

    if not hasattr(dataset.traces[0], hdr):
        raise ValueError(f"Unknown header: {hdr}")

    value = start
    for trace in dataset.traces:
        setattr(trace, hdr, value)
        value += step
