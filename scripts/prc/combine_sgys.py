from pathlib import Path

from seistoolkit.models import Dataset
from seistoolkit.tools.geodesy import compute_cumdist, get_geometry
from seistoolkit.tools.hdrs import hdr_enum
from seistoolkit.tools.io import sgy_input, sgy_output
from seistoolkit.utils import (
    create_folder,
    get_files,
    select_folder,
    sep_files,
    timer,
)


def is_compatible(datasets):
    """Check whether datasets are compatible for joint processing."""
    bin_dt_check = set()
    tr_dt_check = set()
    trace_numsmp = []

    for dataset in datasets:
        bin_dt_check.add(dataset.dt_us)

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

    text_hdr = " "

    return Dataset(
        "merged",
        text_hdr, ">",
        first.dt_us,
        max_numsmp,
        combined_traces
    )


@timer
def main():
    """Combine multiple SEG-Y datasets into seismic lines ."""
    folder_path = select_folder(
        "Please, select 'Groups' folder with groups.")

    group_paths = get_files(folder_path, (".txt",))

    output_folder = create_folder("combined_lines", folder_path)

    groups_list = []
    for group_path in group_paths:
        group = []
        with open(group_path, "r", encoding="utf-8") as f:
            for line in f:
                group.append(Path(line.strip()))
        groups_list.append(group)

    for group_number, group in enumerate(groups_list):
        datasets_group = [sgy_input(file) for file in group]
        combined_dataset = combine_datasets(datasets_group)

        cumdists, _ = compute_cumdist(get_geometry(combined_dataset))

        for cumdist, trace in zip(cumdists, combined_dataset.traces):
            trace.trc_type = cumdist

        combined_dataset.sort_traces("trc_type")

        combined_dataset.set_hdr({"trc_type": 1})

        hdr_enum(combined_dataset, "TRACENO")
        combined_dataset.copy_hdr("TRACENO", ["FFID", "SOURCE", "CDP"])

        # output file name = first file in merged group
        output_path = output_folder / f"{group[0].stem}.sgy"

        # add merged lines list in textual header
        text_hdr = "MERGED LINES:\n"
        for file in group:
            text_hdr += f"{file.name}\n"

        sgy_output(
            combined_dataset,
            output_path,
            sac=-100,
            saed=-100,
            text_hdr=text_hdr
        )

        print(f"Group {group_number + 1} exported successfully!")


if __name__ == "__main__":
    main()
    print("Select folder (unmerged files), then single lines list", end="\n\n")
    sep_files(operation="copy")
    print(f"Done! Complited in {main.elapsed_time:.3f} sec", end="\n\n")
