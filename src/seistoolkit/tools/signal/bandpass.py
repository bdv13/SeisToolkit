import numpy as np

from seistoolkit.models import Dataset


def _validate_bandpass_args(
    dataset: Dataset,
    freqs: tuple[float, float, float, float],
    taper_percent: float,
) -> None:
    """Validate band-pass filter arguments."""

    f1, f2, f3, f4 = freqs

    if not dataset.traces:
        raise ValueError("Dataset contains no traces.")

    if not 0 <= taper_percent < 50:
        raise ValueError("taper_percent must be between 0 and 50.")

    if dataset.numsmp < 32:
        raise ValueError("Trace too short for filtering.")

    if f1 < 0:
        raise ValueError("Frequencies must be non-negative.")

    if not (f1 < f2 <= f3 < f4):
        raise ValueError("Frequencies must satisfy f1 < f2 <= f3 < f4.")

    if dataset.dt_us <= 0:
        raise ValueError("Invalid sample interval.")

    if f4 >= dataset.nyquist:
        raise ValueError(
            f"Maximum frequency ({f4} Hz) exceeds Nyquist frequency "
            f"({dataset.nyquist:.1f} Hz)."
        )


def _calculate_taper_samples(numsmp: int, taper_percent: float) -> int:
    """Calculate number of taper samples on each side."""
    return int(round(numsmp * taper_percent / 100))


def _add_tapered_padding(data: np.ndarray, taper_samples: int) -> np.ndarray:
    """Add tapered padding to reduce FFT edge artifacts."""
    if data.size == 0:
        raise ValueError("Trace data is empty.")
    if taper_samples < 0:
        raise ValueError("taper_samples must be >= 0.")
    if taper_samples == 0:
        return data
    if taper_samples * 2 >= len(data):
        raise ValueError("taper_samples must be < than half of trace length.")

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


def _remove_padding(
    data: np.ndarray,
    taper_samples: int,
) -> np.ndarray:
    """Remove tapered padding from both sides of a trace."""
    if data.size == 0:
        raise ValueError("Trace data is empty.")
    if taper_samples < 0:
        raise ValueError("taper_samples must be >= 0.")
    if taper_samples == 0:
        return data
    if taper_samples * 2 >= len(data):
        raise ValueError("taper_samples must be < than half of trace length.")

    return data[taper_samples:-taper_samples]


def _build_bandpass_response(
    numsmp: int,
    dt_us: float,
    freqs: tuple[float, float, float, float],
) -> np.ndarray:
    """Build band-pass frequency response."""

    f1, f2, f3, f4 = freqs

    # Positive frequency bins corresponding to np.fft.rfft().
    frequency_axis = np.fft.rfftfreq(numsmp, dt_us / 1_000_000)

    # Initialize the frequency response with zero gain.
    response = np.zeros_like(frequency_axis)

    # Build a trapezoidal band-pass response with
    # Hann-tapered transition bands.
    # - Hann taper from 0 to 1 over [f1, f2];
    # - unity gain over [f2, f3];
    # - Hann taper from 1 to 0 over [f3, f4].

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
    """Apply a band-pass filter to a single trace."""

    # Add tapered padding.
    tapered_trace = _add_tapered_padding(data, taper_samples)

    # Apply band-pass frequency response in the frequency domain.
    filt_spectrum = np.fft.rfft(tapered_trace)

    if filt_spectrum.shape != response.shape:
        raise RuntimeError(
            "Frequency response length does not match FFT spectrum."
        )

    filt_spectrum *= response

    # Transform spectrum to time domain and remove artificial taper padding
    filtered_trace = _remove_padding(
        np.fft.irfft(filt_spectrum, n=fft_length), taper_samples
    )

    if filtered_trace.shape != data.shape:
        raise RuntimeError("Trace length changed after bandpass filtering.")

    return filtered_trace


def bandpass_filter(
    dataset: Dataset,
    freqs: tuple[float, float, float, float],
    taper_percent: float = 10.0,
) -> None:
    """Apply a band-pass filter to all traces."""

    # Validate input parameters
    _validate_bandpass_args(dataset, freqs, taper_percent)

    # Build band-pass frequency response.
    taper_samples = _calculate_taper_samples(dataset.numsmp, taper_percent)
    fft_length = dataset.numsmp + 2 * taper_samples
    response = _build_bandpass_response(fft_length, dataset.dt_us, freqs)

    # Apply bandpass filter to each trace in dataset
    for trace in dataset.traces:
        trace.data = _apply_bandpass(
            trace.data,
            response,
            taper_samples,
            fft_length
        )
