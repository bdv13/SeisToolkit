# SeisToolkit
Python tools for SEG-Y inspection, headers and seismic processing

## Tools:

- SEG-Y I/O;
- Trace headers import/export
- SEG-Y files general information table;
- Resort traces;
- Trace length;
- DC removal;
- Bandpass filter;
- Apply statics from header;
- Datasets difference;
- Trace stacking;
- Trace header averager;
- Trace headers manipulations;
- NMEA string parser (GGA, ZDA strings);
- Export survey tracklines (*csv, *gpkg);
- Automatic SEG-Y parts finder;
- Combine several SEG-Y files in one dataset

SeisToolkit
├── scripts
│   ├── check_diff.py
│   ├── combine_sgys.py
│   ├── combine_shots.py
│   ├── correct_interp.py
│   ├── export_nav.py
│   ├── format_bath.py
│   ├── parts_finder.py
│   ├── proc_ebcdics.py
│   ├── proc_nmealog.py
│   ├── sgy_info.py
│   ├── tmp_batch_proc.py
│   └── tmp_single_proc.py
├── src
│   └── seistoolkit
│       ├── proc
│       │   ├── __init__.py
│       │   ├── apply_statics.py
│       │   ├── bandpass.py
│       │   ├── dc_removal.py
│       │   ├── display.py
│       │   ├── subtract_datasets.py
│       │   └── trace_stacking.py
│       ├── __init__.py
│       ├── config.py
│       ├── geometry.py
│       ├── headers.py
│       ├── models.py
│       ├── sbpicker.py
│       ├── segy.py
│       └── utils.py
├── tests
│   ├── test_data
│   ├── __init__.py
│   ├── conftest.py
│   └── test_seistoolkit.py
├── .gitignore
├── LICENSE
├── pyproject.toml
├── README.md
└── uv.lock