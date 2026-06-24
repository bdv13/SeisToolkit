import os
from tkinter import Tk, filedialog, simpledialog, messagebox, ttk
from pyproj import CRS, Transformer

# Export bath from seismic in csv format (File,X,Y,Z)

# 1) Select folder with exported headers from RadExPro:
# SOU_X (projected coords)
# SOU_Y (projected coords)
# SOU_H2OD (fbpick in depth positive - SOU_H2OD=SOU_H2OD/1000*1500/2)

# 2) Select UTM zone

# 3) Select static shift to data (if needed)

# 4) Results will appear in output folder


def find_col(header, *names):
    for n in names:
        if n in header:
            return header.index(n)
    raise ValueError(f"None of columns found: {names}")


def deg_to_dms_str(val):
    d = int(abs(val))
    m = int((abs(val) - d) * 60)
    s = (abs(val) - d - m / 60) * 3600
    return f'{d}°{m:02d}\'{s:06.3f}"'  # оставляем " в конце


# --- Tkinter ---
root = Tk()
root.withdraw()

folder = filedialog.askdirectory(title="Select folder with TXT files")
if not folder:
    exit()

zone = simpledialog.askstring(
    "UTM Zone",
    "Enter UTM zone (01N..60N or 1S..60S)"
)

if not zone or len(zone) < 2:
    messagebox.showerror("Error", "Invalid UTM zone")
    exit()

shift = simpledialog.askfloat(
    "Shift data",
    "Enter shift value",
    initialvalue=0
)

# --- Progress window ---
progress_win = Tk()
progress_win.title("Processing")
progress_win.geometry("450x80")
progress_win.resizable(False, False)
progress_win.protocol("WM_DELETE_WINDOW", lambda: None)  # блокировка крестика

label = ttk.Label(progress_win, text="Processing files...")
label.pack(pady=5)

progress = ttk.Progressbar(
    progress_win,
    orient="horizontal",
    length=260,
    mode="determinate"
)
progress.pack(pady=5)

# --- UTM CRS ---
num = int(zone[:-1])
hem = zone[-1].upper()
epsg = 32600 + num if hem == "N" else 32700 + num

transformer = Transformer.from_crs(
    CRS.from_epsg(epsg),
    CRS.from_epsg(4326),
    always_xy=True
)

# --- Output folder ---
out_dir = os.path.join(folder, "output")
os.makedirs(out_dir, exist_ok=True)

files = [f for f in os.listdir(folder) if f.lower().endswith(".txt")]
progress["maximum"] = len(files)

if not files:
    progress_win.destroy()
    messagebox.showwarning("Warning", "No TXT files found")
    exit()

# --- Processing files ---
for i, fname in enumerate(files, start=1):
    in_path = os.path.join(folder, fname)
    out_path = os.path.join(out_dir, fname.replace(".txt", ".csv"))

    with open(in_path, newline="", encoding="utf-8") as fin, \
         open(out_path, "w", newline="", encoding="utf-8-sig") as fout:

        header = fin.readline().strip().split("\t")

        x_idx = find_col(header, "SOU_X", "CDP_X")
        y_idx = find_col(header, "SOU_Y", "CDP_Y")
        z_idx = find_col(header, "SOU_H2OD")

        # записываем заголовок
        fout.write("File,X,Y,Z\n")

        for line in fin:
            parts = line.strip().split("\t")
            lon, lat = transformer.transform(float(parts[x_idx]), float(parts[y_idx]))
            z = -float(parts[z_idx]) + shift
            fout.write(f'{os.path.splitext(fname)[0]},{deg_to_dms_str(lon)},{deg_to_dms_str(lat)},{z:.2f}\n')

    label.config(text=f"Processing: {fname}")
    progress["value"] = i
    progress_win.update_idletasks()

progress_win.destroy()
messagebox.showinfo("Done", "Conversion finished successfully!")
