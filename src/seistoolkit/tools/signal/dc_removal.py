from typing import Literal

import numpy as np

from seistoolkit.models import Dataset


def _validate_remove_dc_args(
    dataset: Dataset,
    start_ms: float,
    end_ms: float | None,
    method: Literal["mean", "median"],
) -> None:
    """Validate DC removal arguments."""
    if method not in {"mean", "median"}:
        raise ValueError("method must be either 'mean' or 'median'.")

    if not dataset.traces:
        raise ValueError("Dataset contains no traces.")

    duration_ms = dataset.numsmp * dataset.dt_us / 1000

    if not 0 <= start_ms <= duration_ms:
        raise ValueError(f"start_ms must be 0 - {duration_ms:.3f} ms.")

    if end_ms is not None:
        if not start_ms < end_ms <= duration_ms:
            raise ValueError(
                f"end_ms must be between start_ms and {duration_ms:.3f} ms."
            )


def remove_dc(
    dataset: Dataset,
    start_ms: float = 0.0,
    end_ms: float | None = None,
    method: Literal["mean", "median"] = "mean",
) -> None:
    """Remove DC offset from each trace."""

    # Validate input parameters
    _validate_remove_dc_args(dataset, start_ms, end_ms, method)

    # DC estimation window
    dt_ms = dataset.dt_us / 1000
    start_sample = round(start_ms / dt_ms)
    end_sample = dataset.numsmp if end_ms is None else round(end_ms / dt_ms)

    if start_sample >= end_sample:
        raise ValueError("DC estimation window contains no samples.")

    # Estimate and remove DC offset
    reducer = np.mean if method == "mean" else np.median

    for trace in dataset.traces:
        dc = reducer(trace.data[start_sample:end_sample])
        trace.data -= dc
