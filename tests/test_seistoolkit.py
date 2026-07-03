import os
from pathlib import Path

import stk.utils as u
from scripts.export_nav import export_nav
from scripts.proc_nmealog import proc_nmea_log
from stk.headers import hdrs_export
from stk.io_data import sgy_input, sgy_output


def test_io():
    file_path = Path(r"tests\test_data\Line_001.sgy")
    output_path = os.path.join(Path(file_path).parent, "test_output.sgy")
    test_dataset = sgy_input(file_path)
    sgy_output(test_dataset, output_path)
    u.delete(Path(r"tests\test_data\test_output.sgy"))


def test_log_parsing():
    file_path = Path(r"tests\test_data\Log_2026-06-02_32917.nmea")
    proc_nmea_log(Path(file_path))
    u.delete(Path(r"tests\test_data\Log_2026-06-02_32917_parsed.txt"))


def test_export_geom():
    file_path = Path(r"tests\test_data")
    export_nav(file_path)
    u.delete(Path(r"tests\test_data\output"))


def test_export_hdrs():
    file_path = Path(r"tests\test_data\Line_001.sgy")
    output_path = r"tests\test_data\headers.txt"
    dataset = sgy_input(file_path)
    hdrs_export(dataset, output_path, ["FFID", "SOU_X", "SOU_Y", "YEAR", "DAY"])
    u.delete(Path(output_path))

# from stk.geometry import remove_duplicates, linear_interp

# test_data = [
#     (1.34, 1.87),
#     (1.34, 1.87), # duplicate
#     (1.78, 1.44),
#     (1.23, 2.66),
#     (1.23, 2.66), # duplicate
#     (2.07, 2.93),
#     (3.56, 2.11),
#     (3.88, 3.14), # duplicate
#     (3.88, 3.14), # duplicate
#     (3.88, 3.14), # duplicate
#     (12.58, 13.03),
#     (13.19, 14.72),
#     (14.66, 14.11), # duplicate
#     (14.66, 14.11), # duplicate
#     (14.66, 14.11), # duplicate
# ]

# print(test_data)

# remove_duplicates(test_data)
# print(test_data)

# linear_interp(test_data)
# print(test_data)