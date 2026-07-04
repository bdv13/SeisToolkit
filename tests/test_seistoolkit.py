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


