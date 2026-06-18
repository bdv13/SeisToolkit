import utils as u
from sgyfile import SGYFile
from geometry import export_csv, TracksExporter
from config import proj_set

TracksExporter = TracksExporter(proj_set['proj_crs'])

@u.timer
def main(folder_path=None):

    if folder_path is None:
        folder_path = u.get_folder()

    number_files, file_paths = u.get_file_path(folder_path)
    proj_dir_path = u.create_proj_dir()
    log_path = u.create_log_file(proj_dir_path)

    for idx, file_path in enumerate(file_paths, 1):

        current_file = SGYFile(file_path)
        current_file.process()
        u.write_log_file(current_file, log_path)

        export_csv(current_file, proj_dir_path)

        TracksExporter.add_dataset(current_file)

        print(
            f"File {idx:>03} of {number_files}: {current_file.name} "
            f"- Processed! (Size: {current_file.size_mb} Mb)"
        )

    # export all lines in 1 file:
    TracksExporter.export(proj_dir_path)
    
if __name__ == "__main__":
    main()
    print(f"Time: {main.elapsed_time:.3f} sec")
