import pytest
from pathlib import Path


@pytest.fixture
def data_root():
    """Root folder with test data."""
    return Path(__file__).resolve().parent / "test_data"


@pytest.fixture
def nmea_file(data_root):
    path = data_root / "Log.nmea"
    assert path.exists(), f"Missing test file: {path}"
    return path


@pytest.fixture
def sgy_file(data_root):
    path = data_root / "Line_001.sgy"
    assert path.exists(), f"Missing test file: {path}"
    return path