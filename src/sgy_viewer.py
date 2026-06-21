import matplotlib.pyplot as plt
import numpy as np


def plot_seismic(dataset, clip=0.99):

    data = dataset.seisdata.T

    vmax = np.quantile(np.abs(data), clip)

    nt, ntr = data.shape
    time_axis = np.arange(nt) * dataset.dt_ms

    plt.figure(figsize=(14, 6))

    plt.imshow(
        data,
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
