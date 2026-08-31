from typing import Literal

import numpy as np

from seistoolkit.config import ELEV_COORD_PRECISION, SCALED_HDRS
from seistoolkit.models import Dataset, Trace
from seistoolkit.tools.hdrs import hdr_enum

STACK_MEAN_HDRS = (*SCALED_HDRS["sac"], *SCALED_HDRS["saed"])


def _hdrs_merging(
    traces: list[Trace],
    tr_window: int,
) -> list[dict]:
    """Merge trace headers for spatial stacking."""
    merged_hdrs = []

    for start in range(0, len(traces), tr_window):
        hdr_block = traces[start : start + tr_window]
        center_trace = hdr_block[len(hdr_block) // 2]
        merged_hdr = center_trace.__dict__.copy()
        merged_hdr.pop("data", None)

        for hdr_name in STACK_MEAN_HDRS:
            merged_hdr[hdr_name] = round(
                float(
                    np.mean(
                        [
                            getattr(trace, hdr_name)
                            for trace in hdr_block
                        ]
                    )
                ),
                ELEV_COORD_PRECISION,
            )

        merged_hdrs.append(merged_hdr)

    return merged_hdrs


def _data_stacking(
    data: np.ndarray,
    tr_window: int,
    method: Literal["mean", "median"] = "mean",
) -> np.ndarray:
    """Stack neighboring traces using statistical method."""
    if data.ndim != 2:
        raise ValueError("Input data must be 2D array.")

    if data.shape[0] == 0:
        raise ValueError("Input data contains no traces.")

    if not isinstance(tr_window, int):
        raise TypeError("Trace window must be an integer.")

    if tr_window < 2:
        raise ValueError("Trace window must be >= 2.")

    if method not in ("mean", "median"):
        raise ValueError("Method must be 'mean' or 'median'.")

    stack_func = {
        "mean": np.mean,
        "median": np.median,
    }[method]

    stacked = []

    for start in range(0, data.shape[0], tr_window):
        tr_block = data[start : start + tr_window]
        stacked.append(stack_func(tr_block, axis=0))

    return np.stack(stacked)


def trace_stacking(
    dataset: Dataset,
    tr_window: int = 2,
    method: Literal["mean", "median"] = "mean",
) -> None:
    """Stack neighboring traces in place."""
    if not dataset.traces:
        raise ValueError("Dataset contains no traces.")

    stacked_data = _data_stacking(
        dataset.trace_data(),
        tr_window,
        method,
    )
    merged_hdrs = _hdrs_merging(
        dataset.traces,
        tr_window,
    )

    if len(merged_hdrs) != len(stacked_data):
        raise ValueError(
            "Number of merged headers does not match stacked traces."
        )

    dataset.traces = [
        Trace(hdr, data)
        for hdr, data in zip(merged_hdrs, stacked_data)
    ]

    hdr_enum(dataset, "TRACENO")

    dataset.copy_hdr(
        "TRACENO",
        [
            "FFID",
            "CDP",
            "SOURCE",
            "ILINE_NO",
        ],
    )

    dataset.set_hdr(
        {
            "TRC_TYPE": 1,
            "CHAN": 1,
            "XLINE_NO": 1,
            "SAC": 1,
            "SAED": 1,
        }
    )
