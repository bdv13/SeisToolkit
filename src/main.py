from pathlib import Path

from geometry import export_csv
from sgyfile import SGYFile
from utils import (
    create_log_file,
    get_file_path,
    get_folder,
    write_log_file,
)


def main(folder_path=None):

    # 1) Select folder and get file paths
    if folder_path is None:
        folder_path = get_folder()

    number_files, file_paths = get_file_path(folder_path)

    # 2) Сreate log file
    log_path = create_log_file()

    # 3) Create output folter (if it doesn't exist)
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # 4) Batch Process files
    counter = 0
    for idx, file_path in enumerate(file_paths, 1):

        current_file = SGYFile(file_path)
        current_file.get_name()
        current_file.get_size_mb()
        current_file.get_text_hdr()
        current_file.get_bin_hdr()
        current_file.get_byte_order()
        current_file.get_dt_ms()
        current_file.get_ns()
        current_file.get_trlen_ms()
        current_file.get_sample_frequency_hz()
        current_file.get_fmt_code()
        current_file.get_fmt_name()
        current_file.get_bps()
        current_file.get_tr_hdrs()
        current_file.get_tr_num()
        current_file.get_ffids()
        current_file.get_geometry()

        geom_file_path = output_dir / f"{current_file.name}_geom.csv"
        export_csv(current_file, geom_file_path)

        write_log_file(current_file, log_path)

        counter += 1
        print(
            f"File {counter:>03} of {number_files}: {current_file.name} "
            f"- Processed! (Size: {current_file.size_mb} Mb)"
        )


if __name__ == "__main__":
    main()
