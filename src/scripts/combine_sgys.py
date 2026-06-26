from pathlib import Path
import shutil

import stk.utils as u
from stk.models import Dataset
from stk.geometry import compute_cumdist, get_geometry
from stk.headers import create_text_hdr, hdr_enumerator
from stk.io_data import sgy_input, sgy_output


def separate_files(operation='copy'):

    folder_path = Path(u.get_folder())
    files_list = Path(u.get_file())

    output_folder = u.create_folder('separated_files', folder_path)

    with open(files_list, 'r', encoding='utf-8') as f:
        files = [line.strip() for line in f if line.strip()]

    for file in files:

        file_name = Path(file).name

        source_file = folder_path / file_name
        destination_file = Path(output_folder) / file_name

        if not source_file.exists():
            print(f'File not found: {source_file}')
            continue

        if operation == 'copy':
            shutil.copy2(source_file, destination_file)

        elif operation == 'cut':
            shutil.move(source_file, destination_file)

        else:
            raise ValueError("Unknown command!")


def is_compatible(datasets):

    bin_dt_check = set()
    tr_dt_check = set()
    trace_numsmp = []

    for dataset in datasets:
        bin_dt_check.add(dataset.dt)

        for trace in dataset.traces:
            tr_dt_check.add(trace.dt)
            trace_numsmp.append(trace.numsmp)

    if len(bin_dt_check) != 1 or len(tr_dt_check) != 1:
        return False

    return max(trace_numsmp)


def combine_datasets(datasets: list[Dataset]) -> Dataset:
    """Combine several datasets into one dataset."""

    max_numsmp = is_compatible(datasets)
    if max_numsmp is False:
        raise ValueError("Not compatible datasets!")

    first = datasets[0]

    for dataset in datasets:
        for trace in dataset.traces:
            numsmp_diff = max_numsmp - trace.numsmp
            if numsmp_diff:
                trace.zero_pad(numsmp_diff)

    combined_traces = [tr for ds in datasets for tr in ds.traces]

    text_hdr = create_text_hdr()

    return Dataset(
        "merged",
        text_hdr,
        ">",
        first.dt,
        max_numsmp,
        combined_traces
    )


@u.timer
def main():

    folder_path = u.get_folder()
    group_paths = u.get_paths(folder_path, (".txt",))
    output_folder = u.create_folder('combined_lines', folder_path)

    groups_list = []
    for group_path in group_paths:
        group = []
        with open(group_path, "r", encoding="utf-8") as f:
            for line in f:
                group.append(line.strip())
        groups_list.append(group)

    for group_number, group in enumerate(groups_list):
        datasets_group = [sgy_input(file) for file in group]
        combined_dataset = combine_datasets(datasets_group)

        cumdists, steps = compute_cumdist(get_geometry(combined_dataset))

        for cumdist, trace in zip(cumdists, combined_dataset.traces):
            trace.trc_type = cumdist

        combined_dataset.sort_traces('trc_type')

        for trace in combined_dataset.traces:
            trace.trc_type = 0

        hdr_enumerator(combined_dataset, "TRACENO")
        hdr_enumerator(combined_dataset, "FFID")
        hdr_enumerator(combined_dataset, "SOURCE")

        output_path = output_folder / f"Line_{group_number}.sgy"
        sgy_output(combined_dataset, output_path)

        print(f'Group {group_number} exported successfully!')


if __name__ == "__main__":
    print()
    print("Please, select 'Groups' folder with groups.", end="\n\n")
    main()
    print()
    print(f"Done! Complited in {main.elapsed_time:.3f} sec", end="\n\n")
    print("Select folder (unmerged files), then single lines list", end="\n\n")
    separate_files()
    print("Done!")


