from pathlib import Path

import seistoolkit.utils as u
from seistoolkit.geometry import deg_to_dms, utm_to_wgs84

HEADER = "File,X,Y,Z\n"
UTM_ZONE = "49N"
SHIFT = 0


def _formatter(
    file_name: str,
    input_path: Path,
    output_path: Path,
    utm_zone: str,
    shift: float = 0,
    x_col: int = 0,
    y_col: int = 1,
    bath_col: int = 2,
) -> tuple[int, int]:

    with (
        open(input_path, "r", newline="", encoding="utf-8") as fin,
        open(output_path, "w", newline="", encoding="utf-8-sig") as fout,
    ):
        fout.write(HEADER)
        next(fin, None)

        lines_total = 0
        lines_missed = 0

        for line in fin:
            lines_total += 1
            cols = line.strip().split("\t")
            try:
                lat, lon = utm_to_wgs84(cols[x_col], cols[y_col], utm_zone)
                z = -float(cols[bath_col]) + shift
            except ValueError, IndexError:
                lines_missed += 1
                continue

            fout.write(f"{file_name},{deg_to_dms(lon)},{deg_to_dms(lat)},{z:.2f}\n")

        return lines_total, lines_missed


def main() -> None:
    """Format exported bath data."""
    folder_path = u.select_folder()
    file_paths = u.get_paths(folder_path, (".txt",))
    output_folder = u.create_folder("bath", folder_path)

    total = 0
    missed = 0

    for file_path in file_paths:
        file_name = file_path.stem
        output_path = output_folder / f"{file_name}.txt"
        t, m = _formatter(file_name, file_path, output_path, UTM_ZONE, SHIFT)
        total += t
        missed += m

    print(f"Done! Processed: {total}, errors: {missed}", end="\n")


if __name__ == "__main__":
    print()
    print("Please, select folder with files:", end="\n")
    main()
