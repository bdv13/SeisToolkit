import stk.utils as u
from stk.io_data import sgy_input, sgy_output
from stk.geometry import get_geometry, remove_duplicates, linear_interp
from stk.headers import hdr_enumerator, hdr_averager


@u.timer
def proc_flow():
    """Batch seismic processing flow."""

    # Select folder with *.sgy files:
    folder_path = u.select_folder()
    file_paths = u.get_paths(folder_path)
    output_dir = u.create_folder('output', folder_path)

    # Import data:
    for file_path in file_paths:
        dataset = sgy_input(file_path)

        # ----- START of Processing Block -----

        dataset.sort_traces('TRACENO')

        hdr_enumerator(dataset, 'TRACENO')
        dataset.copy_hdr('TRACENO', ['SOURCE', 'CDP', 'FFID'])
        dataset.set_hdr({'CHAN': 1, 'TRC_TYPE': 1, 'OFFSET': 0,})

        coordinates = get_geometry(dataset)
        remove_duplicates(coordinates)
        linear_interp(coordinates)

        for trace, coordinate in zip(dataset.traces, coordinates):
            trace.sou_x, trace.sou_y = coordinate

        hdr_averager(dataset, 'SOU_X', 25)
        dataset.copy_hdr('SOU_X', ['REC_X', 'CDP_X'])

        hdr_averager(dataset, 'SOU_Y', 25)
        dataset.copy_hdr('SOU_Y', ['REC_Y', 'CDP_Y'])

        # ----- END of Processing Block -----

        # Export data:
        output_path = output_dir / f'{dataset.name}.sgy'
        sgy_output(dataset, output_path, sac=-100, saed=-100)

        print(f"{dataset.name} is processed!")


if __name__ == "__main__":
    print()
    proc_flow()
    print(f"Done! Complited in {proc_flow.elapsed_time:.3f} sec", end="\n\n")
