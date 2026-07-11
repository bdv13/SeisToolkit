import numpy as np

from stk.models import Dataset


def _validate_bandpass_args(
        dataset: Dataset,
        freqs: tuple[float, float, float, float],
        taper_percent: float,
        threads: int,
) -> None:
    """Validate band-pass filter arguments."""

    f1, f2, f3, f4 = freqs

    if not dataset.traces:
        raise ValueError("Dataset contains no traces.")

    if not 0 <= taper_percent < 50:
        raise ValueError("taper_percent must be between 0 and 50.")

    if threads < 1:
        raise ValueError("threads must be >= 1.")

    if f1 < 0:
        raise ValueError("Frequencies must be non-negative.")

    if not (f1 < f2 <= f3 < f4):
        raise ValueError("Frequencies must satisfy f1 < f2 <= f3 < f4.")

    if dataset.dt <= 0:
        raise ValueError("Invalid sample interval.")

    nyquist = 1_000_000 / dataset.dt / 2

    if f4 >= nyquist:
        raise ValueError(
            f"Maximum frequency ({f4} Hz) exceeds "
            f"Nyquist frequency ({nyquist:.1f} Hz)."
        )


def _calculate_taper_samples(numsmp: int, taper_percent: float) -> int:
    """Calculate number of taper samples on each side."""
    return int(round(numsmp * taper_percent / 100))


def _add_taper(data: np.ndarray, taper_samples: int) -> np.ndarray:
    """Add cosine tapered padding to both sides of a trace."""
    if data.size == 0:
        raise ValueError("Trace data is empty.")
    if taper_samples < 0:
        raise ValueError("taper_samples must be >= 0.")
    if taper_samples == 0:
        return data
    if taper_samples * 2 >= len(data):
        raise ValueError(
            "taper_samples must be smaller than half of trace length."
        )

    # Generate cosine taper coefficients from 0 to 1.
    taper = np.sin(
        np.linspace(
            0,
            np.pi / 2,
            taper_samples + 1,
        )
    )[1:]

    # Create left and right tapered extensions.
    left_pad = data[0] * taper
    right_pad = data[-1] * taper[::-1]

    return np.concatenate((left_pad, data, right_pad))


def _remove_taper(
        data: np.ndarray,
        taper_samples: int,
) -> np.ndarray:
    """Remove cosine tapered padding from both sides of a trace."""
    if data.size == 0:
        raise ValueError("Trace data is empty.")
    if taper_samples < 0:
        raise ValueError("taper_samples must be >= 0.")
    if taper_samples == 0:
        return data
    if taper_samples * 2 >= len(data):
        raise ValueError(
            "taper_samples must be smaller than half of trace length."
        )

    return data[taper_samples:-taper_samples]


def _build_ormsby_response(
        numsmp: int,
        dt: int,
        freqs: tuple[float, float, float, float],
) -> np.ndarray:
    """Build Ormsby band-pass frequency response."""

    f1, f2, f3, f4 = freqs

    # Positive frequency bins corresponding to np.fft.rfft().
    frequency_axis = np.fft.rfftfreq(numsmp, dt / 1_000_000)

    # Initialize the frequency response with zero gain.
    response = np.zeros_like(frequency_axis)

    # Build the Ormsby frequency response:
    # - Hanning taper from 0 to 1 over [f1, f2];
    # - unity gain over [f2, f3];
    # - Hanning taper from 1 to 0 over [f3, f4].

    left_slope = (frequency_axis >= f1) & (frequency_axis < f2)
    left_slope_fraction = (frequency_axis[left_slope] - f1) / (f2 - f1)
    response[left_slope] = 0.5 * (1 - np.cos(np.pi * left_slope_fraction))

    pass_band = (frequency_axis >= f2) & (frequency_axis <= f3)
    response[pass_band] = 1.0

    right_slope = (frequency_axis > f3) & (frequency_axis <= f4)
    right_slope_fraction = (frequency_axis[right_slope] - f3) / (f4 - f3)
    response[right_slope] = 0.5 * (1 + np.cos(np.pi * right_slope_fraction))

    return response


def _apply_bandpass(
        data: np.ndarray,
        response: np.ndarray,
        taper_samples: int,
        fft_length: int,
) -> np.ndarray:
    """Apply Ormsby filter to a single trace."""

    # Add tapering
    tapered_trace = _add_taper(data, taper_samples)

    # Apply Ormsby frequency response in the frequency domain.
    filt_spectrum = np.fft.rfft(tapered_trace)
    filt_spectrum *= response

    # Transform spectrum back to time domain and remove artificial taper padding
    filtered_trace = _remove_taper(
        np.fft.irfft(filt_spectrum, n=fft_length),
        taper_samples
    )

    if filtered_trace.shape != data.shape:
        raise RuntimeError("Trace length changed after bandpass filtering.")

    return filtered_trace


def bandpass_filter(
        dataset: Dataset,
        freqs: tuple[float, float, float, float],
        taper_percent: float = 10.0,
        threads: int = 1
) -> None:
    """Apply an Ormsby band-pass filter to all traces."""

    # Validate input parameters
    _validate_bandpass_args(dataset, freqs, taper_percent, threads)

    # Build Ormsby frequency response.
    taper_samples = _calculate_taper_samples(dataset.numsmp, taper_percent)
    fft_length = dataset.numsmp + 2 * taper_samples
    response = _build_ormsby_response(
        fft_length,
        dataset.dt,
        freqs
    )

    # Apply Ormsby bandpass filter to each trace in dataset
    for trace in dataset.traces:
        trace.data = _apply_bandpass(
            trace.data,
            response,
            taper_samples,
            fft_length
        )
