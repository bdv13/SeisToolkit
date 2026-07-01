import os
from pathlib import Path

import stk.utils as u
from stk.headers import export_hdrs
from stk.io_data import sgy_input, sgy_output
from scripts.proc_nmealog import proc_nmea_log
from scripts.export_nav import export_nav


def test_io():
    file_path = r'tests\test_data\Line_001.sgy'
    output_path = os.path.join(Path(file_path).parent, 'test_output.sgy')
    test_dataset = sgy_input(file_path)
    sgy_output(test_dataset, output_path)
    u.delete(r'tests\test_data\test_output.sgy')


def test_log_parsing():
    file_path = r'tests\test_data\Log_2026-06-02_32917.nmea'
    proc_nmea_log(Path(file_path))
    u.delete(r'tests\test_data\Log_2026-06-02_32917_parsed.txt')


def test_export_geom():
    file_path = r'tests\test_data'
    export_nav(file_path)
    u.delete(r'tests\test_data\output')


def test_export_hdrs():
    file_path = r'tests\test_data\Line_001.sgy'
    output_path = r"tests\test_data\headers.txt"
    dataset = sgy_input(file_path)
    export_hdrs(
        dataset,
        output_path,
        ['FFID', 'SOU_X', 'SOU_Y', 'YEAR', 'DAY']
    )
    u.delete(output_path)
