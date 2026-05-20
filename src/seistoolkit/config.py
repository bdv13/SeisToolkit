hdrs_len_dict = {"text_hdr": 3200, "bin_hdr": 400, "trace_hdr": 240}

sample_format_dict = {
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

bin_hdr_fields_dict = {
    "sample_int_us": (16, 18),
    "samples_per_tr": (20, 22),
    "sample_format_code": (24, 26),
}

log_hdrs = {
    "File": "name",
    "Size_mb": "size_mb",
    "Traces": "tr_num",
    "Byte_order": "byte_order",
    "Sample_format": "sample_format",
    "Length_ms": "tr_length_ms",
    "Sample_int_ms": "sample_int_ms",
    "sample_freq_hz": "sample_freq_hz",
}
