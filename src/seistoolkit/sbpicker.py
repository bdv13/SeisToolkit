from dataclasses import dataclass

import numpy as np
from numba import njit
from scipy.ndimage import median_filter, uniform_filter1d
from scipy.signal import hilbert

from seistoolkit.models import Dataset, Picks

ATTR_WEIGHTS = {
    "reflection_strength": 0.22,
    "reflection_amplitude": 0.23,
    "peak_prominence": 0.15,
    "lateral_continuity": 0.15,
    "phase_coherence": 0.10,
}

_EPS = 1e-12
_NEG_INF = -np.inf


@dataclass(frozen=True)
class SeabedPickerConfig:
    smoothness: float = 0.05
    curvature: float = 0.05
    max_jump: int = 3
    max_slope: int = 3
    peak_window: int = 3
    tracking_window: int = 20
    polarity: str = "positive"
    search_window: tuple[int, int] | None = None


def _robust_normalisation(data: np.ndarray) -> np.ndarray:
    """Normalize attribute using percentile scaling."""
    low = np.percentile(data, 2, axis=1, keepdims=True)
    high = np.percentile(data, 98, axis=1, keepdims=True)
    scale = high - low
    scale[scale < _EPS] = 1
    return np.clip((data - low) / scale, 0, 1)


def envelope(section: np.ndarray) -> np.ndarray:
    """Calculate signal envelope."""
    analytic = hilbert(section, axis=1)
    return np.abs(analytic)


def peak_strength(section: np.ndarray) -> np.ndarray:
    """Estimate local envelope maxima strength."""
    env = envelope(section)
    left = np.roll(env, 1, axis=1)
    right = np.roll(env, -1, axis=1)
    peak = env - (left + right) / 2
    return np.maximum(peak, 0)


def instantaneous_phase(section: np.ndarray) -> np.ndarray:
    """Calculate instantaneous phase."""
    analytic = hilbert(section, axis=1)
    return np.unwrap(np.angle(analytic), axis=1)


def phase_coherence(section: np.ndarray) -> np.ndarray:
    """Measure lateral phase coherence between neighboring traces."""
    analytic = hilbert(section, axis=1)
    phase = np.angle(analytic)
    phase_diff = np.diff(phase, axis=0)
    phase_diff = np.angle(np.exp(1j * phase_diff))
    coherence = np.abs(np.cos(phase_diff))
    return np.pad(coherence, ((1, 0), (0, 0)), mode="edge")


def peak_prominence(section: np.ndarray, window: int = 20) -> np.ndarray:
    """Estimate reflection peak prominence."""
    env = envelope(section)
    background = uniform_filter1d(env, size=window, axis=1)
    return np.maximum(env - background, 0)


def lateral_continuity(section: np.ndarray) -> np.ndarray:
    """Measure amplitude similarity between neighboring traces."""
    norm = section / (np.max(np.abs(section), axis=1, keepdims=True) + _EPS)
    diff = np.abs(np.diff(norm, axis=0))
    continuity = 1 / (uniform_filter1d(diff, size=5, axis=0) + _EPS)
    return np.pad(continuity, ((1, 0), (0, 0)), mode="edge")


def reflection_amplitude(section: np.ndarray, mode="positive"):
    if mode == "positive":
        return np.maximum(section, 0)
    if mode == "negative":
        return np.maximum(-section, 0)
    return np.abs(section)


@njit
def _track_numba(
    score: np.ndarray,
    smoothness: float,
    curvature: float,
    max_jump: int,
    max_slope: int,
) -> np.ndarray:
    """Track optimal path using dynamic programming."""

    n_traces, n_samples = score.shape

    cost = np.full(score.shape, np.inf)
    parent = np.zeros(score.shape, dtype=np.int32)
    slope = np.zeros(score.shape, dtype=np.int32)

    cost[0] = -score[0]

    for tr in range(1, n_traces):
        new_cost = np.full(n_samples, np.inf)
        new_parent = np.zeros(n_samples, dtype=np.int32)
        new_slope = np.zeros(n_samples, dtype=np.int32)

        for sample in range(n_samples):
            start = max(0, sample - max_jump)
            stop = min(n_samples, sample + max_jump + 1)

            best_cost = np.inf
            best_idx = start

            for idx in range(start, stop):
                jump = idx - sample
                if abs(jump) > max_slope:
                    continue

                diff = jump - slope[tr - 1, idx]

                value = (
                    cost[tr - 1, idx]
                    + smoothness * jump * jump
                    + curvature * diff * diff
                )

                if value < best_cost:
                    best_cost = value
                    best_idx = idx

            new_cost[sample] = best_cost - score[tr, sample]
            new_parent[sample] = best_idx
            new_slope[sample] = sample - best_idx

        cost[tr] = new_cost
        parent[tr] = new_parent
        slope[tr] = new_slope

    samples = np.empty(n_traces, dtype=np.int32)

    samples[-1] = np.argmin(cost[-1])

    for tr in range(n_traces - 1, 0, -1):
        samples[tr - 1] = parent[tr, samples[tr]]

    return samples


class SeabedPicker:
    """Automatic seabed horizon tracker."""

    def __init__(self, config: SeabedPickerConfig | None = None):
        if config is None:
            config = SeabedPickerConfig()
        self.config = config

    def _compute_attributes(
        self,
        section: np.ndarray
    ) -> dict[str, np.ndarray]:
        """Calculate horizon tracking attributes."""
        return {
            "reflection_strength": envelope(section),
            "reflection_amplitude": reflection_amplitude(
                section, self.config.polarity
            ),
            "peak_prominence": peak_strength(section),
            "phase_coherence": phase_coherence(section),
            "lateral_continuity": lateral_continuity(section),
        }

    def _track(self, score: np.ndarray) -> np.ndarray:
        """Track optimal path through score matrix."""
        return _track_numba(
            score,
            self.config.smoothness,
            self.config.curvature,
            self.config.max_jump,
            self.config.max_slope,
        )

    def _limit_tracking_window(
        self,
        score: np.ndarray,
        samples: np.ndarray,
    ) -> np.ndarray:
        """Restrict search around initial horizon."""
        restricted = np.full_like(score, _NEG_INF)
        for tr, sample in enumerate(samples):
            start = max(0, sample - self.config.tracking_window)
            stop = min(score.shape[1], sample + self.config.tracking_window + 1)
            restricted[tr, start:stop] = score[tr, start:stop]
        return restricted

    def _refine_horizon(self, attrs, samples):
        refined = samples.copy()
        local_score = (
            attrs["reflection_amplitude"]
            * attrs["phase_coherence"]
            * attrs["peak_prominence"]
        )
        for tr, sample in enumerate(samples):
            start = max(0, sample - self.config.peak_window)
            stop = min(local_score.shape[1], sample + self.config.peak_window + 1)
            refined[tr] = start + np.argmax(local_score[tr, start:stop])
        return refined

    def autopick(self, dataset: Dataset) -> Picks:
        """Automatically track seabed reflection horizon."""

        section = dataset.trace_data()
        attrs = self._compute_attributes(section)

        score = np.zeros_like(section)

        for name, attr in attrs.items():
            score += _robust_normalisation(attr) * ATTR_WEIGHTS[name]

        if self.config.search_window is not None:
            start, stop = self.config.search_window

            score[:, :start] = _NEG_INF
            score[:, stop:] = _NEG_INF

        samples = self._track(score)
        samples0 = median_filter(samples, size=7)
        score = self._limit_tracking_window(score, samples0)
        samples = self._track(score)
        samples = self._refine_horizon(attrs, samples)

        pick_hdrs = {
            "FFID": [tr.ffid for tr in dataset.traces],
            "CHAN": [tr.chan for tr in dataset.traces],
        }

        return Picks(pick_hdrs, samples, dataset.dt_us)
