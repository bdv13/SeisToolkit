import stk.utils as u
from stk.io_data import sgy_input, sgy_output

from proc.subtract_datasets import subtract_datasets
from proc.display import seismic_display


@u.timer
def check_diff():
    """Calculate difference between two datasets."""

    file1_path = u.select_file()
    file2_path = u.select_file()
    output_path = file1_path.parent / f"{file1_path.stem}_diff.sgy"

    dataset1 = sgy_input(file1_path)
    dataset2 = sgy_input(file2_path)

    dataset_diff = subtract_datasets(dataset1, dataset2)

    seismic_display(dataset_diff)

    sgy_output(dataset_diff, output_path, -100, -100)


if __name__ == "__main__":
    print()
    check_diff()
    print(f"Done! Complited in {check_diff.elapsed_time:.3f} sec", end="\n\n")
