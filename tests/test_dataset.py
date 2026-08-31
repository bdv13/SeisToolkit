import numpy as np
import pytest

from seistoolkit.models import Dataset, Trace


@pytest.fixture
def sample_dataset():
    traces = [
        Trace(
            {"ffid": 1, "dt": 4, "numsmp": 3, "sac": 1, "saed": 1},
            np.array([1.0, 2.0, 3.0]),
        ),
        Trace(
            {"ffid": 2, "dt": 4, "numsmp": 3, "sac": 1, "saed": 1},
            np.array([4.0, 5.0, 6.0]),
        ),
    ]
    return Dataset("demo", "text header", ">", 4000, 3, traces)


def test_dataset_section_shape(sample_dataset):
    section = sample_dataset.section

    assert isinstance(section, np.ndarray)
    assert section.shape == (sample_dataset.numsmp, len(sample_dataset.traces))
    np.testing.assert_array_equal(section[:, 0], [1.0, 2.0, 3.0])
    np.testing.assert_array_equal(section[:, 1], [4.0, 5.0, 6.0])


def test_dataset_set_section_updates_trace_data(sample_dataset):
    new_section = np.array([[10.0, 20.0], [30.0, 40.0], [50.0, 60.0]])

    sample_dataset.set_section(new_section)

    np.testing.assert_array_equal(sample_dataset.section, new_section)


def test_dataset_zero_pad_adds_samples_at_end(sample_dataset):
    sample_dataset.zero_pad(2)

    assert sample_dataset.numsmp == 5
    assert len(sample_dataset.traces[0].data) == 5
    np.testing.assert_array_equal(
        sample_dataset.traces[0].data, [1.0, 2.0, 3.0, 0.0, 0.0]
    )


def test_dataset_zero_pad_negative_raises(sample_dataset):
    with pytest.raises(ValueError, match="num_samples must be >= 0"):
        sample_dataset.zero_pad(-1)


def test_dataset_clip_removes_samples(sample_dataset):
    sample_dataset.clip(1)

    assert sample_dataset.numsmp == 2
    np.testing.assert_array_equal(sample_dataset.traces[0].data, [1.0, 2.0])


def test_dataset_clip_exceeds_length_raises(sample_dataset):
    with pytest.raises(ValueError, match="num_samples exceeds trace length"):
        sample_dataset.clip(10)


def test_dataset_record_length_updates_trace_count(sample_dataset):
    sample_dataset.record_length(20, unit="ms")

    assert sample_dataset.numsmp == 5
    assert len(sample_dataset.traces[0].data) == 5


def test_dataset_filter_traces_keeps_matching_values(sample_dataset):
    sample_dataset.filter_traces("ffid", [1], include=True)

    assert len(sample_dataset.traces) == 1
    assert sample_dataset.traces[0].ffid == 1


def test_dataset_filter_traces_removes_matching_values(sample_dataset):
    sample_dataset.filter_traces("ffid", [1], include=False)

    assert len(sample_dataset.traces) == 1
    assert sample_dataset.traces[0].ffid == 2


def test_dataset_nyquist_uses_dt_us(sample_dataset):
    expected = 1_000_000 / (2 * sample_dataset.dt_us)

    assert sample_dataset.nyquist == expected
