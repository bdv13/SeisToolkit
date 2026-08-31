from seistoolkit.tools.io import sgy_input, sgy_output
from seistoolkit.utils import create_folder, get_files, select_folder, timer


@timer
def processing_flow():
    """Batch seismic processing flow."""

    # ----- Select folder with *.sgy files -----
    folder_path = select_folder('Select folder with *.sgy files')
    file_paths = get_files(folder_path)
    output_dir = create_folder(folder_path, 'output')

    # ----- Import data ------------------------
    counter = 0
    for file_path in file_paths:
        dataset = sgy_input(file_path)

        # ----- START of Processing Block -----

        # ----- END of Processing Block -------

        # ----- Export data -------------------
        output_path = output_dir / f'{dataset.name}_prc.sgy'
        sgy_output(dataset, output_path, -100, -100)

        counter += 1

        print(f"{dataset.name} is processed ({counter})!")


if __name__ == "__main__":
    processing_flow()
    print(f'Done! Complited in {processing_flow.elapsed_time:.3f} sec')
