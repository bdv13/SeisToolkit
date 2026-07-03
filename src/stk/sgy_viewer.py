from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import stk.utils as u
from stk.io_data import sgy_input


def plot_seismic(dataset, clip: float = 0.99) -> None:
    """Display a seismic section."""
    section = dataset.to_section()

    vmax = np.quantile(np.abs(section), clip)

    nt, ntr = section.shape
    time_axis = np.arange(nt) * dataset.dt / 1000

    plt.figure(figsize=(14, 6))

    plt.imshow(
        section,
        cmap="seismic_r",
        aspect="auto",
        vmin=-vmax,
        vmax=vmax,
        extent=[0, ntr, time_axis[-1], time_axis[0]]
    )

    plt.title("Seismic section")
    plt.xlabel("Trace")
    plt.ylabel("TWT (ms)")

    plt.colorbar(label='Amplitude')
    plt.show()


@u.timer
def sgy_view(file_path: Path | None = None) -> None:

    if file_path is None:
        file_path = u.select_file()

    dataset = sgy_input(file_path)

    plot_seismic(dataset)


if __name__ == "__main__":
    sgy_view()
    print(f"Done! Complited in {sgy_view.elapsed_time:.3f} sec", end="\n\n")
