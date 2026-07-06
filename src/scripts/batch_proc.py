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
        seismic_line = sgy_input(file_path)

        # ----- START of Processing Block -----

        hdr_enumerator(seismic_line, 'TRACENO')
        hdr_enumerator(seismic_line, 'FFID')
        hdr_enumerator(seismic_line, 'CDP')

        line_geom = get_geometry(seismic_line)
        remove_duplicates(line_geom)
        linear_interp(line_geom)

        for trace, coordinate in zip(seismic_line.traces, line_geom):
            trace.sou_x, trace.sou_y = coordinate
            trace.rec_x, trace.rec_y = coordinate
            trace.cdp_x, trace.cdp_y = coordinate

        hdr_averager(seismic_line, 'SOU_X', 25)
        hdr_averager(seismic_line, 'SOU_Y', 25)

        seismic_line.sort_traces("CDP")

        # ----- END of Processing Block -----

        # Export data:
        output_path = output_dir / f'{seismic_line.name}.sgy'
        sgy_output(seismic_line, output_path, sac=-100, saed=-100)

        print(f"{seismic_line.name} is processed!")


if __name__ == "__main__":
    print()
    proc_flow()
    print(f"Done! Complited in {proc_flow.elapsed_time:.3f} sec", end="\n\n")
