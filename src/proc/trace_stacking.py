import numpy as np


def trace_stacking(
        data: np.ndarray,
        stack_size: int,
) -> np.ndarray:
    """Stack neighboring traces by mean value."""

    if data.ndim != 2:
        raise ValueError("Input data must be 2D array.")

    if data.shape[0] == 0:
        raise ValueError("Input data contains no traces.")

    if not isinstance(stack_size, int):
        raise TypeError("Stack size must be an integer.")

    if stack_size < 2:
        raise ValueError("Stack size must be >= 2.")

    n_traces = data.shape[0]

    stacked = []

    for start in range(0, n_traces, stack_size):
        trace_block = data[start:start + stack_size]

        stacked.append(
            np.mean(trace_block, axis=0)
        )

    return np.asarray(stacked)