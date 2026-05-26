from config import proj_settings
from geometry import TrackExporter, compute_cumdist, export_csv
from sgyfile import SGYFile
from utils import (
    create_log_file,
    create_proj_dir,
    get_file_path,
    get_folder,
    timer,
    write_log_file,
)


@timer
def main(folder_path=None):

    # 1) Select folder and get file paths
    # 2) Create project folter (if it doesn't exist)
    # 3) Сreate log file
    # 4) Create class for tracklines export
    # 5) Batch Process files

    if folder_path is None:
        folder_path = get_folder()
    number_files, file_paths = get_file_path(folder_path)
    proj_dir_path = create_proj_dir()
    log_path = create_log_file(proj_dir_path)
    tracks_exporter = TrackExporter(crs=proj_settings["proj_crs"])

    for idx, file_path in enumerate(file_paths, 1):
        current_file = SGYFile(file_path)
        current_file.get_name()
        current_file.set_id(idx)
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
        compute_cumdist(current_file)
        current_file.get_line_len()
        current_file.get_mean_step()
        current_file.get_delay_flag()

        geom_file_path = proj_dir_path / f"{current_file.name}_geom.csv"
        export_csv(current_file, geom_file_path)

        tracks_exporter.add_dataset(current_file)

        write_log_file(current_file, log_path)

        print(
            f"File {idx:>03} of {number_files}: {current_file.name} "
            f"- Processed! (Size: {current_file.size_mb} Mb)"
        )

    tracklines_path = proj_dir_path / f"{proj_settings['proj_name']}_lines.gpkg"
    tracks_exporter.export(tracklines_path)


if __name__ == "__main__":
    main()
    print(f"Time: {main.elapsed_time:.3f} sec")
