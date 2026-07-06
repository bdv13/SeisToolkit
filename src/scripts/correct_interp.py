import stk.utils as u
from stk.io_data import sgy_input

X_COL, Y_COL, LINE_COL, MATCH_COL = range(4)


@u.timer
def main(match_field="source"):
    """Script for fixing X,Y in Kingdom 2D interpretation line file."""

    print('Started...')

    interp = u.select_file()
    sgy_folder = u.select_folder()

    sgy_paths = u.get_paths(sgy_folder)

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
    print('Select file with interpretation, then select folder with sgy files.')
    main()
    print(f"Done! Complited in {main.elapsed_time:.3f} sec", end="\n\n")
