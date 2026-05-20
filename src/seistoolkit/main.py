from seistoolkit.sgyfile import SGYFile
from seistoolkit.utils import (
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

    # 3) Batch Process files
    counter = 0
    for idx, file_path in enumerate(file_paths, 1):

        current_file = SGYFile(file_path)
        current_file.set_name()
        current_file.get_size_mb()
        current_file.get_text_hdr()
        current_file.get_bin_hdr()
        current_file.get_byte_order()
        current_file.get_sample_int_ms()
        current_file.get_samples_per_trace()
        current_file.get_trace_length_ms()
        current_file.get_sample_frequency_hz()
        current_file.get_sample_format_code()
        current_file.get_sample_format()
        current_file.get_bytes_per_sample()
        current_file.get_tr_hdrs()
        current_file.get_tr_num()

        write_log_file(current_file, log_path)

        counter += 1
        print(
            f"File {counter:>03} of {number_files}: {current_file.name} "
            f"- Processed! (Size: {current_file.size_mb} Mb)"
        )


if __name__ == "__main__":
    main()
