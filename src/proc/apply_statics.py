from stk.models import Dataset


def apply_statics(
        dataset: Dataset,
        header: str,
        invert: bool = False
) -> None:
    """
    Apply static corrections stored in a trace header.
    Static values are interpreted as milliseconds.
    If `invert` is True, static corrections are applied with the opposite sign.
    """

    header = header.lower()

    if not hasattr(dataset.traces[0], header):
        raise AttributeError(f"Trace has no header '{header}'")

    for trace in dataset.traces:
        static_ms = getattr(trace, header)

        if invert:
            static_ms = -static_ms

        shift_samples = int(round(static_ms * 1000 / dataset.dt_us))

        if shift_samples >= 0:
            trace.zero_pad(shift_samples, side="start")
            trace.clip(shift_samples, side="end")
        else:
            shift_samples = -shift_samples
            trace.clip(shift_samples, side="start")
            trace.zero_pad(shift_samples, side="end")
