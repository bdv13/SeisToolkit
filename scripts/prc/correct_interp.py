from seistoolkit.tools.io import sgy_input
from seistoolkit.utils import get_files, select_file, select_folder, timer

X_COL, Y_COL, LINE_COL, MATCH_COL = range(4)


@timer
def main(match_field="source"):
    """Script for fixing X,Y in Kingdom 2D interpretation line file."""

    print("Started...")

    interp = select_file()
    sgy_folder = select_folder()

    sgy_paths = get_files(sgy_folder)

    geometry = {}
    for sgy_path in sgy_paths:
        dataset = sgy_input(sgy_path)
        for trace in dataset.traces:
            geometry[(sgy_path.stem, getattr(trace, match_field))] = (
                trace.sou_x,
                trace.sou_y,
            )

    output = interp.with_stem(f"{interp.stem}_updated")

    with open(interp) as fin, open(output, "w") as fout:
        for row in fin:
            cols = row.split()
            key = (cols[LINE_COL], int(float(cols[MATCH_COL])))

            if (coords := geometry.get(key)) is not None:
                x, y = coords
                cols[X_COL] = f"{x:.2f}"
                cols[Y_COL] = f"{y:.2f}"

            fout.write(" ".join(cols) + "\n")


if __name__ == "__main__":
    print()
    print("Select file with interpretation, then folder with sgy files.")
    main()
    print(f"Done! Complited in {main.elapsed_time:.3f} sec", end="\n\n")
