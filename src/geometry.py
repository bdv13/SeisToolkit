import pandas as pd


def export_csv(dataset, path):
    df = pd.DataFrame(
        {
            "Line": dataset.name,
            "FFID": dataset.ffids,
            "SOU_X": dataset.sou_x_list,
            "SOU_Y": dataset.sou_y_list,
            "SAC": dataset.sac,
            "UNITS": dataset.units,
        }
    )
    df["SOU_X"] = df["SOU_X"].map(lambda x: f"{x:.2f}")
    df["SOU_Y"] = df["SOU_Y"].map(lambda x: f"{x:.2f}")
    df.to_csv(path, index=False, encoding="utf-8")
