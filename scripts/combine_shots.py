from pathlib import Path

import seistoolkit.utils as u
from seistoolkit.config import DEFAULT_TEXT_HDR, MAX_SEGY_SAMPLES
from seistoolkit.models import Dataset
from seistoolkit.segy import sgy_input, sgy_output


def _sgy_compatibility(file_paths: list[Path]) -> tuple[int, int]:
    """Return the maximum number of samples and dt if SEG-Y files."""
    if not file_paths:
        raise ValueError("No SEG-Y files provided.")

    bin_dt_check = set()
    tr_dt_check = set()
    max_numsmp = 0

    print("Checking compatibility...")

    for file_path in file_paths:
        dataset = sgy_input(file_path, headers_only=True)

        bin_dt_check.add(dataset.dt_us)

        for trace in dataset.traces:
            tr_dt_check.add(trace.dt)
            max_numsmp = max(max_numsmp, trace.numsmp)

    if len(bin_dt_check) != 1:
        raise ValueError("Binary headers have different sample intervals.")

    if len(tr_dt_check) != 1:
        raise ValueError("Trace headers have different sample intervals.")

    dt = next(iter(tr_dt_check))

    print(f"All traces have the same dt (us): {dt}. "
          f"Maximum numsmp is {max_numsmp}"
    )

    return max_numsmp, dt


def _combine_shots(file_paths: list[Path], output_path: Path) -> None:
    """Merge several SEG-Y files into one SGE-Y file."""
    if not file_paths:
        raise ValueError("No SEG-Y files provided.")

    max_numsmp, dt = _sgy_compatibility(file_paths)

    if max_numsmp > MAX_SEGY_SAMPLES:
        print(
            f"Warning: {max_numsmp} samples exceed SEG-Y compatibility limit. "
            f"Truncating to {MAX_SEGY_SAMPLES} samples."
        )
        max_numsmp = MAX_SEGY_SAMPLES

    total_shots = len(file_paths)

    merged_dataset = Dataset("data", DEFAULT_TEXT_HDR, ">", dt, max_numsmp, [])
    sgy_output(merged_dataset, output_path, -100, -100)

    with open(output_path, "ab") as merged:
        counter = 0
        for file_path in file_paths:
            dataset = sgy_input(file_path, normalize_hdrs=False)

            for trace in dataset.traces:
                if trace.numsmp > max_numsmp:
                    diff = trace.numsmp - max_numsmp
                    trace.clip(diff)

                elif trace.numsmp < max_numsmp:
                    diff = max_numsmp - trace.numsmp
                    trace.zero_pad(diff)

                merged.write(trace.export_tr_hdr())
                merged.write(trace.export_tr_data())

            counter += 1
            percent = counter / total_shots * 100

            print(
                f"\rMerged {counter}/{total_shots} ({percent:.2f}%)".ljust(40),
                end="",
                flush=True,
            )

    print()


def main(folder_path=None):
    """Merge SGY files into one SGY file."""
    if not folder_path:
        folder_path = u.select_folder()

    file_paths = u.get_paths(folder_path)
    output_path = folder_path / "merged.sgy"

    _combine_shots(file_paths, output_path)


if __name__ == "__main__":
    print("Please, select forlder with shots (sgy files):", end="\n")
    main()
    print("Done!", end="\n")
