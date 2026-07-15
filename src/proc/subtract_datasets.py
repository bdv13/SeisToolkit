from copy import deepcopy

from stk.models import Dataset


def _validate_difference_args(
    dataset1: Dataset,
    dataset2: Dataset,
) -> None:

    if not dataset1.traces:
        raise ValueError("First dataset contains no traces.")

    if not dataset2.traces:
        raise ValueError("Second dataset contains no traces.")

    if len(dataset1.traces) != len(dataset2.traces):
        raise ValueError("Datasets contain different numbers of traces.")

    if dataset1.numsmp != dataset2.numsmp:
        raise ValueError("Datasets have different numbers of samples.")

    if dataset1.dt_us != dataset2.dt_us:
        raise ValueError("Datasets have different sample intervals.")


def subtract_datasets(
    dataset1: Dataset,
    dataset2: Dataset,
) -> Dataset:
    """Return wavefield difference between two datasets."""
    _validate_difference_args(dataset1, dataset2)

    dataset = deepcopy(dataset1)

    for trace, trace1, trace2 in zip(
        dataset.traces,
        dataset1.traces,
        dataset2.traces,
    ):
        trace.data = trace1.data - trace2.data

    return dataset
