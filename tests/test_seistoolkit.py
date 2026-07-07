import numpy as np
import pytest

from scripts.export_nav import export_nav
from scripts.proc_nmealog import proc_nmea_log
from stk.headers import hdrs_export
from stk.io_data import sgy_input, sgy_output


def test_io(tmp_path, sgy_file):
    output_path = tmp_path / "test_output.sgy"
    dataset = sgy_input(sgy_file)
    sgy_output(dataset, output_path)
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_log_parsing(tmp_path, nmea_file):
    file_path = tmp_path / "Log.nmea"
    file_path.write_bytes(nmea_file.read_bytes())
    proc_nmea_log(file_path)
    out = file_path.with_name(file_path.stem + "_parsed.txt")
    assert out.exists()


def test_export_geom(tmp_path, sgy_file):
    input_file = tmp_path / "Line_001.sgy"
    input_file.write_bytes(sgy_file.read_bytes())
    export_nav(tmp_path)
    out_dir = tmp_path / "output"
    assert out_dir.exists()


def test_export_hdrs(tmp_path, sgy_file):
    output_path = tmp_path / "headers.txt"
    dataset = sgy_input(sgy_file)
    hdrs_export(dataset, output_path, ["FFID", "SOU_X", "SOU_Y", "YEAR", "DAY"])
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
