import numpy as np


def hdr_averager(dataset, hdr: str, window: int) -> None:
    """Apply moving average to a trace header."""
    hdr = hdr.lower()

    if window < 1:
        raise ValueError("window must be >= 1")
    if window % 2 == 0:
        window += 1

    if not hasattr(dataset.traces[0], hdr):
        raise ValueError(f"Unknown header: {hdr}")

    values = np.array(
        [getattr(trace, hdr) for trace in dataset.traces], dtype=float
    )

    pad = window // 2
    padded = np.pad(values, (pad, pad), mode="edge")

    kernel = np.ones(window, dtype=float) / window
    averaged = np.convolve(padded, kernel, mode="valid")

    for trace, value in zip(dataset.traces, averaged):
        setattr(trace, hdr, value)
