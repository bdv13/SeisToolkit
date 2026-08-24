import math
import os
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial import KDTree

import seistoolkit.utils as u
from seistoolkit.geometry import get_geometry
from seistoolkit.segy import sgy_input


def extract_nav(file_paths: list, output_file: Path):

    rows = []

    for file_path in file_paths:
        current_dataset = sgy_input(file_path)
        file_name = current_dataset.name
        coordinates = get_geometry(current_dataset)

        for i, trace in enumerate(current_dataset.traces):
            x, y = coordinates[i]

            rows.append(
                {
                    "LINE": file_name,
                    "FFID": trace.ffid,
                    "SOU_X": x,
                    "SOU_Y": y,
                }
            )

    nav_df = pd.DataFrame(rows)

    nav_df["SOU_X"] = nav_df["SOU_X"].round(3)
    nav_df["SOU_Y"] = nav_df["SOU_Y"].round(3)

    nav_df.to_csv(output_file, index=False, sep="\t", encoding="utf-8")


def is_overlap_exceeded(
    line_a,
    line_b,
    tolerance,
    max_overlap_traces=5,
):
    """Return True if overlap exceeds the allowed number of traces."""
    points_a = line_a["points"]
    points_b = line_b["points"]

    # Direction of line A
    origin = points_a[0]
    direction = points_a[-1] - origin

    length = np.linalg.norm(direction)

    if length == 0:
        return False

    direction /= length

    # Project points onto the direction of line A
    proj_a = (points_a - origin) @ direction
    proj_b = (points_b - origin) @ direction

    a_end = proj_a.max()

    # Only B traces located within A's longitudinal range
    overlap_points = points_b[
        (proj_b >= 0) & (proj_b <= a_end)
    ]

    if len(overlap_points) == 0:
        return False

    # Check which B traces are spatially close to A
    tree = KDTree(points_a)
    distances, _ = tree.query(overlap_points)

    overlap_traces = np.count_nonzero(
        distances <= tolerance
    )

    return overlap_traces > max_overlap_traces


def find_parts(
    nav_file,
    res_file,
    tolerance=5,
    max_overlap_tr=10,
) -> None:

    nav_df = pd.read_csv(nav_file, sep="\t")

    lines = {}

    for name, group in nav_df.groupby("LINE"):
        points = group[["SOU_X", "SOU_Y"]].to_numpy()

        lines[name] = {
            "start": tuple(points[0]),
            "end": tuple(points[-1]),
            "points": points,
        }

    line_names = list(lines.keys())
    start_points = [lines[name]["start"] for name in line_names]

    tree = KDTree(start_points)

    connections = {name: set() for name in line_names}

    overlap_rej_count = 0

    for name_a in line_names:
        a = lines[name_a]

        distances, idxs = tree.query(
            a["end"],
            k=len(line_names),
            distance_upper_bound=tolerance,
        )

        for dist, j in zip(distances, idxs):
            if j == len(line_names) or math.isinf(dist):
                continue

            name_b = line_names[j]

            if name_a == name_b:
                continue

            d_forward = math.hypot(
                a["end"][0] - lines[name_b]["start"][0],
                a["end"][1] - lines[name_b]["start"][1],
            )

            d_backward = math.hypot(
                a["start"][0] - lines[name_b]["end"][0],
                a["start"][1] - lines[name_b]["end"][1],
            )

            if d_forward < d_backward and d_forward < tolerance:

                if is_overlap_exceeded(
                    lines[name_a],
                    lines[name_b],
                    tolerance,
                    max_overlap_tr,
                ):
                    overlap_rej_count += 1
                    continue

                connections[name_a].add(name_b)
                connections[name_b].add(name_a)

    groups = []
    visited = set()

    for name in line_names:
        if name in visited:
            continue

        stack = [name]
        group = set()

        while stack:
            cur = stack.pop()

            if cur in visited:
                continue

            visited.add(cur)
            group.add(cur)
            stack.extend(connections[cur] - visited)

        groups.append(sorted(group))

    groups_sorted = sorted(
        groups,
        key=lambda g: (-len(g), g),
    )

    print(
        f"{overlap_rej_count} connections were not made "
        f"due to overlap."
    )

    # Save results:
    with open(res_file, "w", encoding="utf-8") as f:
        for i, g in enumerate(groups_sorted, 1):
            g_no_ext = [os.path.splitext(name)[0] for name in g]
            f.write(f"Group {i} ({len(g_no_ext)}): [{', '.join(g_no_ext)}]\n")

    # Plot results:
    plt.figure(figsize=(8, 6))

    for group in groups_sorted:
        color = "red" if len(group) > 1 else "blue"

        for line_name in group:
            line_df = nav_df[nav_df["LINE"] == line_name]
            plt.plot(
                line_df["SOU_X"],
                line_df["SOU_Y"],
                color=color, linewidth=1
            )

    plt.legend(
        handles=[
            mpatches.Patch(color="red", label="Connected lines (>1)"),
            mpatches.Patch(color="blue", label="Single lines"),
        ]
    )

    plt.title(f"Lines grouped (Tolerance = {tolerance}m)")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.axis("equal")
    plt.show()


def create_pathslist(prefix, res_file, group_folder, single_lines_file):

    single_lines = []
    group_counter = 0

    with open(res_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip().startswith("Group"):
                continue

            if "[" not in line or "]" not in line:
                continue

            group_number = line.split()[1]

            files_str = line.split("[")[1].split("]")[0]
            file_names = [name.strip() for name in files_str.split(",")]

            # Single lines
            if len(file_names) == 1:
                single_lines.append(file_names[0])
                continue

            group_counter += 1

            group_path = group_folder / f"Group_{group_number}.txt"

            with open(group_path, "w", encoding="utf-8") as group_file:
                for fname in file_names:
                    group_file.write(f"{prefix}\\{fname}.sgy\n")

    # Save single lines
    if single_lines:
        with open(single_lines_file, "w", encoding="utf-8") as f:
            for name in single_lines:
                f.write(f"{prefix}\\{name}.sgy\n")

    print(f"Groups number: {group_counter}")
    print(f"Single lines: {len(single_lines)}")


@u.timer
def main():

    folder_path = u.select_folder()
    file_paths = u.get_paths(folder_path, formats=(".sgy", "segy"))
    output_folder = u.create_folder("output", folder_path)

    nav_file = output_folder / "fparts_nav.txt"
    res_file = output_folder / "fparts_res.txt"
    group_folder = u.create_folder("groups", output_folder)
    single_lines = output_folder / "fparts_single_lines.txt"

    extract_nav(file_paths, nav_file)
    find_parts(nav_file, res_file, tolerance=5, max_overlap_tr=20)
    prefix = folder_path
    create_pathslist(prefix, res_file, group_folder, single_lines)


if __name__ == "__main__":
    print()
    main()
    print()
    print(f"Done! Complited in {main.elapsed_time:.3f} sec", end="\n\n")
