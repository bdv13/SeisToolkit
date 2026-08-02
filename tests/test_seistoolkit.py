from pathlib import Path

import numpy as np
import pytest

from scripts.export_nav import export_nav
from scripts.proc_nmealog import nmea_parser
from seistoolkit.headers import hdrs_export
from seistoolkit.segy import sgy_input, sgy_output


def test_io(tmp_path, sgy_file):
    output_path = tmp_path / "test_output.sgy"
    dataset = sgy_input(sgy_file)
    sgy_output(dataset, output_path)
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_nmea_parser(tmp_path):
    input_file = Path("tests/test_data/Log.nmea")
    output_file = tmp_path / "parsed.txt"
    nmea_parser(input_file, output_file)
    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_export_geom(tmp_path, sgy_file):
    input_file = tmp_path / "Line_001.sgy"
    input_file.write_bytes(sgy_file.read_bytes())
    export_nav(tmp_path)
    out_dir = tmp_path / "output"
    assert out_dir.exists()


def test_export_hdrs(tmp_path, sgy_file):
    output_path = tmp_path / "headers.txt"
    dataset = sgy_input(sgy_file)
    hdrs_export(dataset, output_path, [
        "FFID", "SOU_X", "SOU_Y", "YEAR", "DAY"]
    )
    assert output_path.exists()


def test_dataset_section(sgy_file):
    dataset = sgy_input(sgy_file)
    section = dataset.section
    assert isinstance(section, np.ndarray)
    assert section.ndim == 2
    assert section.shape == (dataset.numsmp, len(dataset.traces))


def test_dataset_set_section(sgy_file):
    dataset = sgy_input(sgy_file)
    section = dataset.section.copy()
    new_section = section * 2
    dataset.set_section(new_section)
    np.testing.assert_array_equal(dataset.section, new_section)


def test_dataset_set_section_wrong_shape(sgy_file):
    dataset = sgy_input(sgy_file)
    wrong = np.zeros((10, 10))
    with pytest.raises(ValueError):
        dataset.set_section(wrong)


def test_dataset_set_section_wrong_dim(sgy_file):
    dataset = sgy_input(sgy_file)
    wrong = np.zeros(100)
    with pytest.raises(ValueError):
        dataset.set_section(wrong)
