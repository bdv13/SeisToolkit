from pathlib import Path

from seistoolkit.models import Dataset


def sgy_output(
    dataset: Dataset,
    output_path: Path,
    sac: int = 1,
    saed: int = 1,
    text_hdr: str | None = None,
    bin_hdr: dict | None = None,
) -> None:
    """Export dataset object to standard SEG-Y file."""

    dataset.denorm_hdrs(sac=sac, saed=saed)

    try:
        with open(output_path, "wb") as f:
            f.write(dataset.export_text_hdr(text_hdr))
            f.write(dataset.export_bin_hdr(**(bin_hdr or {})))

            for trace in dataset.traces:
                f.write(trace.export_hdrs(dataset.byte_order))
                f.write(trace.export_data(dataset.byte_order))

    finally:
        dataset.norm_hdrs()
