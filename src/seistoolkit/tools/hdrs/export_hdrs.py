from pathlib import Path

from seistoolkit.config import TRACE_HDRS
from seistoolkit.models import Dataset


def export_hdrs(
    dataset: Dataset,
    hdrs: tuple[str, ...],
    output_path: Path,
    sep: str = " ",
    add_file_hdrs: bool = True,
) -> None:
    """Export dataset trace headers in txt file."""

    if not dataset.traces:
        raise ValueError("Dataset contains no traces.")

    for hdr in hdrs:
        if hdr.upper() not in TRACE_HDRS:
            raise ValueError(f"Unknown header {hdr}!")

    with open(output_path, "w", encoding="utf-8") as f:
        if add_file_hdrs:
            f.write(sep.join([hdr.upper() for hdr in hdrs]) + "\n")

        for trace in dataset.traces:
            values = (str(trace.__dict__[hdr.lower()]) for hdr in hdrs)

            f.write(sep.join(values) + "\n")
