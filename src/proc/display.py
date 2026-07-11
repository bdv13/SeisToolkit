import numpy as np
import matplotlib.pyplot as plt


def seismic_display(dataset, clip: float = 0.99) -> None:
    """Display a seismic section."""
    section = dataset.section

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
