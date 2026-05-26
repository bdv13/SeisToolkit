proj_settings = {
    "proj_name": "MyProject",
    "proj_crs": "EPSG:32636",
    "proj_dir": "output",
}

hdrlen_dict = {
    "text_hdr": 3200,  # textual header
    "bin_hdr": 400,  # binary header
    "trace_hdr": 240,  # trace header
}

sample_fmt_dict = {
    1: ("IBM Floating Point", 4),
    2: ("32-bit Integer", 4),
    3: ("16-bit Integer", 2),
    4: ("Fixed-point with gain (obsolete)", None),
    5: ("IEEE Floating point", 4),
    6: ("Not used", None),
    7: ("Not used", None),
    8: ("8-bit Integer", 1),
    9: ("64-bit IEEE Float", 8),
    10: ("32-bit unsigned integer", 4),
    11: ("16-bit unsigned integer", 2),
    12: ("64-bit unsigned integer", 8),
}

bin_dict = {
    "dt": (16, 18),  # sample interval (µs)
    "ns": (20, 22),  # number of samples per trace
    "fmt": (24, 26),  # sample format code
}

tr_dict = {
    "traceno": (0, 4),
    "ffid": (8, 12),
    "chan": (12, 16),
    "source": (16, 20),
    "cdp": (20, 24),
    "trc_type": (28, 30),
    "offset": (36, 40),
    "sou_h2od": (60, 64),
    "sac": (70, 72),
    "sou_x": (72, 76),
    "sou_y": (76, 80),
    "rec_x": (80, 84),
    "rec_y": (84, 88),
    "units": (88, 90),
    "delay": (108, 110),
    "numsmp": (114, 116),
    "dt": (116, 118),
    "year": (156, 158),
    "day": (158, 160),
    "hour": (160, 162),
    "minute": (162, 164),
    "second": (164, 166),
    "cdp_x": (180, 182),
    "cdp_y": (182, 184),
    "iline_no": (188, 192),
    "xline_no": (192, 194),
}

log_dict = {
    "Line": "name",
    "Line_ID": "id",
    "Size_mb": "size_mb",
    "Traces": "tr_num",
    "Byte_order": "byte_order",
    "Sample_format": "fmt_name",
    "Length_ms": "trlen_ms",
    "Sample_int_ms": "dt_ms",
    "Sample_freq_hz": "sample_freq_hz",
    "Length_km": "line_len_km",
    "Shot_int_m": "mean_step",
    "Delay": "delay_flag",
}

units_dict = {
    1: "Meters",
    2: "Arc Seconds",
    3: "Degrees",
    4: "DMS",
}
